"""Native per-ship SU descriptions and build tooltips, gated by Cataclysm."""

import json
import re
from hwrm_common import CACHE, PROJECT, save
from hwrm_inspect import record_config
from production_data import table
from language_data import LANGUAGES, stock_strings, stock_directory

FAMILY_ID = 9684400
TITLE_ID = 9684401
POPUP_TITLE_ID = 9684402
BUILD_NAME_ID = 9684700
BUILD_DESC_ID = 9684900
BUILD_TIMED_ID = 9685100
FIRST_SHIP_ID = 9684500

LABELS = {
    "English": {"su": "SU", "group": "per squadron", "ship": "per ship", "family": "Support Units"},
    "Russian": {"su": "СУ", "group": "за отряд", "ship": "за корабль", "family": "СУ"},
    "French": {
        "su": "US",
        "group": "par escadron",
        "ship": "par vaisseau",
        "family": "Unités de soutien",
    },
    "German": {
        "su": "VE",
        "group": "pro Staffel",
        "ship": "pro Schiff",
        "family": "Versorgungseinheiten",
    },
    "Italian": {
        "su": "US",
        "group": "per squadriglia",
        "ship": "per nave",
        "family": "Unità di supporto",
    },
    "Spanish": {
        "su": "UA",
        "group": "por escuadrón",
        "ship": "por nave",
        "family": "Unidades de apoyo",
    },
}

# The owner requests Latin SU even in Russian; full resource names are translated.
for labels in LABELS.values():
    labels["su"] = "SU"
OWNED_NAMES = {
    "English": "SUPPORT UNITS",
    "Russian": "ЕДИНИЦЫ ПОДДЕРЖКИ",
    "French": "UNITÉS DE SOUTIEN",
    "German": "VERSORGUNGSEINHEITEN",
    "Italian": "UNITÀ DI SUPPORTO",
    "Spanish": "UNIDADES DE APOYO",
}


def description_ids(design):
    return {ident: FIRST_SHIP_ID + i for i, ident in enumerate(sorted(design["ships"]))}


def suffix(row, language):
    labels = LABELS[language]
    head = labels["su"] + ": " + str(row["su_per_group"])
    if row["build_batch"] == 1:
        return head + " " + labels["ship"]
    return (
        head
        + " "
        + labels["group"]
        + " ("
        + str(row["build_batch"])
        + " x "
        + str(row["su_per_hull"])
        + ")"
    )


def generate(out, design, inherited, quote):
    ids = description_ids(design)
    descriptions = {}
    build_rows = {}
    aliases = {ident: ident for ident in ids}
    for ident in ids:
        name = f"ship/{ident}/{ident}.ship"
        fields, _ = record_config(inherited[name].read_text(encoding="utf-8-sig"))
        descriptions[ident] = fields.get("sobDescription", "")
    for race in design["races"]:
        build = table(inherited[f"scripts/races/{race}/scripts/def_build.lua"], "build")
        for row in build.values():
            if row["Type"] == 0 and row["ThingToBuild"].lower() in ids:
                aliases[row["ThingToBuild"]] = row["ThingToBuild"].lower()
                build_rows[row["ThingToBuild"].lower()] = row
    strings = {language: stock_strings(language) for language in LANGUAGES}
    carrier_keys = sorted(
        k
        for k, v in strings["Russian"].items()
        if "транспортн" in v.lower() and "carrier" in strings["English"].get(k, "").lower()
    )
    replacements = {
        "транспортные корабли": "авианосцы",
        "транспортный корабль": "авианосец",
        "транспортного корабля": "авианосца",
        "транспортных кораблях": "авианосцах",
        "транспортных кораблей": "авианосцев",
    }
    for key in carrier_keys:
        value = strings["Russian"][key]
        for old, new in replacements.items():
            value = re.sub(
                old,
                lambda m, v=new: v[0].upper() + v[1:] if m[0][0].isupper() else v,
                value,
                flags=re.I,
            )
        strings["Russian"][key] = value
    name_overrides = json.loads(
        (PROJECT / "localization/russian_ship_names.json").read_text(encoding="utf8")
    )["entries"]
    for key, entry in name_overrides.items():
        native_key = "$" + key
        assert strings["English"][native_key] == entry["english"]
        assert strings["Russian"][native_key] == entry["expected_russian"]
        strings["Russian"][native_key] = entry["russian"]
    renamed_keys = set(carrier_keys) | {"$" + key for key in name_overrides}
    # Replace only the relevant entries in their EXISTING native dictionary files.
    # Keep low stock IDs out of the high-ID Cataclysm dictionary's range.
    for source in stock_directory("Russian").glob("*.ucs"):
        raw = source.read_bytes()
        encoding = "utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "cp1251"
        lines = source.read_bytes().decode(encoding).splitlines(keepends=True)
        changed = False
        for i, line in enumerate(lines):
            match = re.match(r"^(\d+)([ \t]+)([^\r\n]*)([\r\n]*)$", line)
            if match and "$" + match[1] in renamed_keys:
                lines[i] = match[1] + match[2] + strings["Russian"]["$" + match[1]] + match[4]
                changed = True
        if changed:
            target = out / "locale/Russian" / source.name
            target.write_bytes("".join(lines).encode(encoding))
    build_numbers = {ident: i for i, ident in enumerate(sorted(build_rows))}
    # Reject future growth/collisions before a native dictionary is emitted.
    ranges = [
        set((FAMILY_ID, TITLE_ID, POPUP_TITLE_ID)),
        set(ids.values()),
        *[
            set(range(first, first + len(build_rows)))
            for first in (BUILD_NAME_ID, BUILD_DESC_ID, BUILD_TIMED_ID)
        ],
    ]
    occupied = set()
    for block in ranges:
        if occupied.intersection(block):
            raise ValueError("Cataclysm localization ID ranges overlap")
        occupied.update(block)
    if max(occupied) - min(occupied) >= 1024:
        raise ValueError("Cataclysm dictionary exceeds its compact native range")
    for language, native in strings.items():
        if any("$" + str(key) in native for key in occupied):
            raise ValueError("Native dictionary collision: " + language)
    time_values = table(out / "scripts/productiontimes/buildtimes.lua", "buildtimes")
    time_labels = json.loads((PROJECT / "localization/hwmp24.json").read_text(encoding="utf8"))
    report = {}
    for language in LANGUAGES:
        native = strings[language]
        fallback = []

        def resolve(value):
            if not value.startswith("$"):
                return value
            if value in native:
                return native[value]
            if value not in strings["English"]:
                raise ValueError("Missing original ship description: " + value)
            fallback.append(value)
            return strings["English"][value]

        entries = {FAMILY_ID: LABELS[language]["family"], TITLE_ID: OWNED_NAMES[language] + ":"}
        entries[POPUP_TITLE_ID] = (
            "Экипаж" if language == "Russian" else OWNED_NAMES[language]
        ) + ":"
        for ident, number in build_numbers.items():
            row = build_rows[ident]
            base_name = resolve(row.get("DisplayedName", ""))
            base_desc = resolve(row.get("Description", ""))
            su = suffix(design["ships"][ident], language)
            entries[BUILD_NAME_ID + number] = (
                base_name + " [SU: " + str(design["ships"][ident]["su_per_group"]) + "]"
            )
            entries[BUILD_DESC_ID + number] = base_desc + "\\n\\n" + su
            timed = base_desc
            seconds = time_values.get(row["ThingToBuild"])
            if base_desc and seconds is not None:
                labels = time_labels[language]
                timed += (
                    "  \\n\\n<b>"
                    + labels["base_time"]
                    + ":</b>  "
                    + str(seconds)
                    + labels["seconds"]
                )
            entries[BUILD_TIMED_ID + number] = timed + "\\n\\n" + su
        assert "$" + str(TITLE_ID) not in native
        for ident, number in ids.items():
            if "$" + str(number) in native:
                raise ValueError("Native dictionary collision: " + str(number))
            row = design["ships"][ident]
            base = resolve(descriptions[ident])
            # Short leading price remains visible in the native narrow unit-role panel.
            entries[number] = (
                LABELS[language]["su"] + ": " + str(row["su_per_group"]) + " | " + base
            )
        assert "$" + str(FAMILY_ID) not in native
        path = out / f"locale/{language}/hwmp24_cataclysm.ucs"
        records = "".join(
            str(key)
            + "\t"
            + value.replace("\r\n", "\\n").replace("\n", "\\n").replace("\t", " ")
            + "\r\n"
            for key, value in sorted(entries.items())
        )
        path.write_bytes(records.encode("utf-16"))
        lua = out / f"locale/{language}/hwmp24_cataclysm.lua"
        text = lua.read_text(encoding="ascii")
        for variable, first in [
            ("HWMP_CataclysmBuildNames", BUILD_NAME_ID),
            ("HWMP_CataclysmBuildDescriptions", BUILD_DESC_ID),
            ("HWMP_CataclysmBuildTimedDescriptions", BUILD_TIMED_ID),
        ]:
            text += (
                variable
                + " = {\n"
                + "".join(
                    "["
                    + quote(alias)
                    + "]="
                    + quote("$" + str(first + build_numbers[canonical]))
                    + ",\n"
                    for alias, canonical in sorted(aliases.items())
                    if canonical in build_numbers
                )
                + "}\n"
            )
        lua.write_text(text, encoding="ascii", newline="\n")
        report[language] = {"entries": len(entries), "english_fallback": sorted(set(fallback))}
    registry = (CACHE / "players-patch-audit/rm-base/locale/localedat.lua").read_text(
        encoding="ascii"
    )
    assert "hwmp24_cataclysm.dat" not in registry
    end = registry.rfind("}")
    (out / "locale/localedat.lua").write_text(
        registry[:end] + '    {name="hwmp24_cataclysm.dat"},\n}\n', encoding="ascii", newline="\n"
    )
    for race in design["races"]:
        folder = out / f"scripts/races/{race}/hwmp_cataclysm"
        (folder / "props").mkdir(parents=True, exist_ok=True)
        (folder / "scripts").mkdir(parents=True, exist_ok=True)
        path = f"data:scripts/races/{race}/hwmp_cataclysm/scripts/def_build.lua"
        (folder / "props/default.lua").write_text(
            "String_Properties_Priority = 20.0\nString_Properties = {path_build = "
            + quote(path)
            + "}\n",
            encoding="ascii",
            newline="\n",
        )
        loader = f'dofilepath("data:scripts/races/{race}/scripts/def_build.lua")\ndofilepath("data:scripts/hwmp24/cataclysm_buildtips.lua")\n'
        (folder / "scripts/def_build.lua").write_text(loader, encoding="ascii", newline="\n")
    helper = PROJECT / "tools/templates/cataclysm_buildtips.lua"
    (out / "scripts/hwmp24/cataclysm_buildtips.lua").write_text(
        helper.read_text(encoding="ascii"), encoding="ascii", newline="\n"
    )
    save(
        PROJECT / "local/cataclysm/descriptions.json",
        {"ships": ids, "languages": report, "native_tested": False},
    )


def patch_deathmatch(text):
    from project_version import VERSION

    hook = (
        '\n    if GameRulesName == "HWMP '
        + VERSION
        + ' Cataclysm" then\n        if HWMP_CataclysmHUDStart == nil then\n            dofilepath("data:scripts/hwmp24/cataclysm_hud.lua")\n        end\n        HWMP_CataclysmHUDStart()\n    end\n'
    )
    old = "\tSpeechRaceHelper()\n"
    assert text.count(old) == 1
    text = text.replace(old, old + hook)
    old = '\t\tRule_AddInterval("timer_updating",1.02)\t--timed with doai\t\n'
    assert text.count(old) == 1
    return text.replace(old, old + hook)
