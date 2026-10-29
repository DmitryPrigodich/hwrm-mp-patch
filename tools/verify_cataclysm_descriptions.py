"""Description, native-dictionary and final callback contracts; no engine claim."""

import re
import json
from lupa.lua51 import LuaRuntime
from cataclysm_descriptions import (
    FAMILY_ID,
    TITLE_ID,
    POPUP_TITLE_ID,
    OWNED_NAMES,
    LABELS,
    description_ids,
    suffix,
    patch_deathmatch,
)
from hwrm_common import CACHE, DONOR, PROJECT, index
from hwrm_inspect import plain
from language_data import stock_strings


def translated(text):
    return re.sub(r"for (\w+, \w+) in (\w+) do", r"for \1 in pairs(\2) do", text)


def verify(out, design):
    files = index(DONOR)
    files.update(index(out))
    ids = description_ids(design)
    registry = LuaRuntime()
    registry.execute((CACHE / "players-patch-audit/rm-base/locale/localedat.lua").read_text())
    original = [row.name for _, row in registry.globals().Dictionaries.items()]
    registry.execute(files["locale/localedat.lua"].read_text())
    assert [row.name for _, row in registry.globals().Dictionaries.items()] == original + [
        "hwmp24_cataclysm.dat"
    ]
    checks = []
    dictionary_keys = None
    for language in LABELS:
        raw = files[f"locale/{language.lower()}/hwmp24_cataclysm.ucs"].read_bytes()
        assert raw[:2] == b"\xff\xfe"
        text = raw.decode("utf-16")
        assert "\n" not in text.replace("\r\n", "")
        pairs = [line.split("\t", 1) for line in text.splitlines()]
        ucs = dict(pairs)
        assert len(pairs) == len(ucs) and len(ucs) > len(ids) + 3
        assert max(map(int, ucs)) - min(map(int, ucs)) < 1024
        assert min(map(int, ucs)) >= 9684400
        if dictionary_keys is None:
            dictionary_keys = set(ucs)
        assert set(ucs) == dictionary_keys
        native = stock_strings(language)
        if language == "Russian":
            for dictionary in (out / "locale/Russian").glob("*.ucs"):
                if dictionary.name.lower() == "hwmp24_cataclysm.ucs":
                    continue
                raw_native = dictionary.read_bytes()
                decoded = raw_native.decode(
                    "utf-16" if raw_native.startswith(b"\xff\xfe") else "cp1251"
                )
                for line in decoded.splitlines():
                    match = re.match(r"^(\d+)\s+(.+)$", line)
                    if match:
                        native["$" + match[1]] = match[2]

        def localized(value):
            return ucs.get(value[1:], native.get(value, value)) if value.startswith("$") else value

        assert (
            ucs[str(POPUP_TITLE_ID)]
            == ("Экипаж" if language == "Russian" else OWNED_NAMES[language]) + ":"
        )
        assert native["$2126"] == ("Авианосцы" if language == "Russian" else native["$2126"])
        assert native["$7054"] == ("Авианосец" if language == "Russian" else native["$7054"])
        if language == "Russian":
            for key, entry in json.loads(
                (PROJECT / "localization/russian_ship_names.json").read_text(encoding="utf8")
            )["entries"].items():
                assert native["$" + key] == entry["russian"]
        assert ucs[str(FAMILY_ID)] == LABELS[language]["family"]
        assert ucs[str(TITLE_ID)] == OWNED_NAMES[language] + ":"
        assert LABELS[language]["su"] == "SU"
        for ident, number in ids.items():
            assert ucs[str(number)].startswith(
                LABELS[language]["su"] + ": " + str(design["ships"][ident]["su_per_group"]) + " | "
            )
        for race in design["races"]:
            vm = LuaRuntime(register_eval=False, register_builtins=False)
            g = vm.globals()
            g.doscanpath = lambda *a: None
            vm.execute("strlower=string.lower;strsub=string.sub")
            g.GetProductionTimeSetting = lambda: 1
            mode = [0]
            assert g.UI_RulesGetNumber is None
            assert g.GetGameSettingAsString is None

            def load(name):
                relative = (
                    "locale/" + language.lower() + "/" + name[7:]
                    if name.startswith("locale:")
                    else name[5:]
                )
                vm.execute(translated(files[relative].read_text(encoding="ascii")))

            g.dofilepath = load
            g.doscanpath = lambda path, pattern: (
                load("data:scripts/productiontimes/applybuildtimes.lua")
                if pattern == "applybuildtimes.lua"
                else None
            )
            # The authoritative ordinary build table is not duplicated by the mode.
            vm.execute(
                (DONOR / f"scripts/races/{race}/scripts/def_build.lua").read_text(encoding="ascii")
            )
            before = plain(g.build)
            load("data:scripts/productiontimes/applybuildtimes.lua")
            assert plain(g.build) == before
            props = LuaRuntime()
            props.execute(
                files[f"scripts/races/{race}/hwmp_cataclysm/props/default.lua"].read_text()
            )
            path = props.globals().String_Properties.path_build
            assert path == f"data:scripts/races/{race}/hwmp_cataclysm/scripts/def_build.lua"
            assert props.globals().String_Properties_Priority > 1
            load(path)
            after = plain(g.build)
            priced = 0
            for i, row in before.items():
                ident = row["ThingToBuild"].lower()
                if ident in ids:
                    priced += 1
                    assert (
                        after[i]["Description"].startswith("$")
                        and after[i]["Description"].isascii()
                    )
                    assert (
                        after[i]["DisplayedName"].startswith("$")
                        and after[i]["DisplayedName"].isascii()
                    )
                    assert localized(after[i]["Description"]).endswith(
                        suffix(design["ships"][ident], language)
                    )
                    assert after[i]["HWMP_CataclysmSU"] == 1
                    remaining = dict(after[i])
                    remaining.pop("HWMP_CataclysmSU")
                    assert localized(after[i]["DisplayedName"]).endswith(
                        "["
                        + LABELS[language]["su"]
                        + ": "
                        + str(design["ships"][ident]["su_per_group"])
                        + "]"
                    )
                    remaining["DisplayedName"] = row.get("DisplayedName")
                    remaining["Description"] = row.get("Description")
                    assert remaining == row
                else:
                    assert after[i] == row
            load("data:scripts/hwmp24/cataclysm_buildtips.lua")
            assert plain(g.build) == after, "Duplicate SU suffix"
            # SU text remains with the optional base-time tooltip feature enabled.
            g.GetProductionTimeSetting = lambda: 2
            load(path)
            assert all(
                suffix(design["ships"][row.ThingToBuild.lower()], language)
                in localized(row.Description)
                for _, row in g.build.items()
                if row.ThingToBuild.lower() in ids
            )
            checks.append(language + "/" + race + ":" + str(priced))

    base = (DONOR / "scripts/rules/deathmatch/deathmatch.lua").read_text(encoding="ascii")
    actual = files["scripts/rules/deathmatch/deathmatch.lua"].read_text(encoding="ascii")
    assert actual == patch_deathmatch(base)
    assert "Rules_GetNumber" not in actual
    for enabled in (0, 1):
        vm = LuaRuntime(register_eval=False, register_builtins=False)
        g = vm.globals()
        starts = []
        g.dofilepath = lambda *a: None
        for name in [
            "HW2_Letterbox",
            "Volume_AddSphere",
            "MPRestrict",
            "SetStartFleetSuffix",
            "UI_SetElementEnabled",
            "UI_TimerStop",
            "Rule_AddInterval",
            "SpeechRaceHelper",
        ]:
            g[name] = lambda *a: 0
        g.GetGameSettingAsNumber = lambda key: 0
        # Match the observed native context: do not invent the missing API.
        assert g.Rules_GetNumber is None
        g.HWMP_CataclysmHUDStart = lambda: starts.append("start")
        g.GameRulesName = "HWMP 2.4.5 Cataclysm" if enabled else "ordinary"
        vm.execute(actual)
        g.OnInit()
        g.OnStartOrLoad()
        vm.execute(actual)  # A repeated base load also keeps the original callbacks intact.
        g.OnInit()
        g.OnStartOrLoad()
        assert len(starts) == (4 if enabled else 0)
    return {
        "status": "passed",
        "selected_ship_descriptions": len(ids),
        "languages": len(LABELS),
        "build_tables_checked": checks,
        "base_time_options": [1, 2],
        "final_callback_load_order_mock": "Pure GameRulesName gate; missing Rules_GetNumber is not supplied",
        "native_tested": False,
    }
