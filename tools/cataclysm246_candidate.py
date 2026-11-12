"""Isolated 2.4.6 prototype from pinned published input. Never installs/launches.

Canonical 2.4.5 generators, balance and publication receipts remain untouched.
The prototype deliberately replaces defective fractional SU with a periodic gate;
atomic admission/reservation of native build queues remains an engine test item.
"""

from tool_safety import ensure_normal_python

ensure_normal_python()

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import re
import shutil
import zipfile

from cataclysm import model
from cataclysm_descriptions import generate as descriptions
from hwrm_common import PROJECT, DONOR, index, save, sha
from hwrm_archive import package_source
from production_data import stock_files

RULE_NAME = "HWMP 2.4.6 Cataclysm Test1"
TITLE = "HWMP Patch 2.4.6 - Cataclysm Test1"
CONFIG = PROJECT / "design/cataclysm246.json"
PROFILES = ("small", "normal", "large", "huge", "vast")


def candidate_model():
    config = json.loads(CONFIG.read_text(encoding="utf8"))
    design = deepcopy(model())
    for ident, cost in config["price_overrides"].items():
        row = design["ships"][ident]
        if not isinstance(cost, int) or cost < 0:
            raise ValueError("Invalid SU price: " + ident)
        row["su_per_hull"] = cost
        row["su_per_group"] = cost * row["build_batch"]
    if not set(config["capacity_providers"]).issubset(design["ships"]):
        raise ValueError("Unpriced capacity provider")
    design["version"] = config["version"]
    return config, design


def write(source, name, text):
    path = source / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="ascii", newline="\n")


def frozen_input(config):
    stage = PROJECT / "local/Workshop-upload" / config["base_content_revision"][:12]
    prepared = json.loads((stage / "preparation.json").read_text(encoding="utf8"))
    if prepared["content_revision"] != config["base_content_revision"]:
        raise ValueError("Wrong base input revision")
    source = stage / "content"
    files = {name: source / name for name in prepared["source_inventory"]}
    if {name: sha(path) for name, path in files.items()} != prepared["source_inventory"]:
        raise ValueError("Published loose source no longer matches its frozen inventory")
    return source, files, prepared["source_inventory"]


def build(package=False):
    config, design = candidate_model()
    baseline, inputs, before = frozen_input(config)
    base_hud = inputs["scripts/hwmp24/cataclysm_hud.lua"].read_text(encoding="ascii")
    frozen_prices = {
        key: int(value) for key, value in re.findall(r'\["([^"]+)"\] = (\d+),', base_hud)
    }
    if frozen_prices != {key: row["su_per_group"] for key, row in model()["ships"].items()}:
        raise ValueError("Canonical base prices changed; review the candidate's pinned inputs")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    work = PROJECT / "local/cataclysm246" / stamp
    source = work / "source"
    release = work / "release"
    source.mkdir(parents=True)
    for name, path in inputs.items():
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

    for ident in design["ships"]:
        relative = f"ship/{ident}/{ident}.ship"
        old = inputs[relative].read_text(encoding="ascii")
        # SU enforcement is entirely script-owned in this explicit experiment.
        # Retain native Carrier/Shipyard/Probe/Research/Layout supplies.
        text, count = re.subn(
            r'(setSupplyValue\(NewShipType, "HWMP_SupportUnits", )[^)]+',
            lambda match: match[1] + "0",
            old,
        )
        if count != 1:
            raise ValueError("Expected one conditional SU assignment: " + ident)
        write(source, relative, text)

    rules = inputs["scripts/rules/hwmpcataclysm.lua"].read_text(encoding="ascii")
    rules = rules.replace(
        'GameRulesName = "HWMP 2.4.5 Cataclysm"', f'GameRulesName = "{RULE_NAME}"'
    )
    # One hidden fixed option; legacy profile files are also made identical below.
    pattern = r'(\{\s*name = "unitcaps",)[\s\S]*?\n    \},'
    replacement = """{\n        name = "unitcaps",\n        locName = "$3214",\n        tooltip = "$3234",\n        default = 0,\n        visible = 0,\n        choices = {"Fixed SU", "Normal"},\n    },"""
    rules, count = re.subn(pattern, lambda _: replacement, rules, count=1)
    if count != 1:
        raise ValueError("Unknown native Unit Cap option structure")
    write(source, "scripts/rules/hwmpcataclysm.lua", rules)

    for profile in PROFILES:
        # Freeze all retained count caps to Normal, regardless of stale lobby settings.
        relative = "scripts/rules/hwmpcataclysm/unitcaps/normal.lua"
        text = inputs[relative].read_text(encoding="ascii")
        text, count = re.subn(r'(supplyLimit\("HWMP_SupportUnits", )[^)]+', r"\g<1>250", text)
        if count != 1:
            raise ValueError("Missing base SU cap")
        text = text.replace(
            "-- Exact binary scale; the player-facing HUD uses ordinary SU.",
            "-- Prototype: zero native SU weights; script gate uses nominal integers.",
        )
        write(source, f"scripts/rules/hwmpcataclysm/unitcaps/{profile}.lua", text)
        for race in design["races"]:
            relative = f"scripts/races/{race}/hwmp_cataclysm/unitcaps/normal.lua"
            text = inputs[relative].read_text(encoding="ascii")
            text += f'\nsupplyLimit("Carrier", {config["carrier_caps"][race]})\nsupplyLimit("Shipyard", {config["shipyard_cap"]})\n'
            write(
                source,
                f"scripts/races/{race}/hwmp_cataclysm/unitcaps/{profile}.lua",
                text,
            )

    costs = (
        "HWMP_CataclysmCosts = {\n"
        + "".join(
            f'    ["{ident}"] = {row["su_per_group"]},\n'
            for ident, row in sorted(design["ships"].items())
        )
        + "}\n"
    )
    types = (
        "HWMP_SU246Types = {\n"
        + "".join(f'    "{ident}",\n' for ident in sorted(design["ships"]))
        + "}\n"
    )
    providers = (
        "HWMP_SU246Providers = {\n"
        + "".join(
            f'    ["{ident}"] = {value},\n'
            for ident, value in sorted(config["capacity_providers"].items())
        )
        + "}\n"
    )
    hud = (PROJECT / "tools/templates/cataclysm246_hud.lua").read_text(encoding="ascii")
    write(
        source,
        "scripts/hwmp24/cataclysm_hud.lua",
        costs
        + types
        + providers
        + f'HWMP_SU246Maximum = {config["maximum_capacity"]}\n'
        + f'HWMP_SU246Interval = {config["update_interval"]}\n'
        + hud,
    )
    relative = "scripts/rules/deathmatch/deathmatch.lua"
    text = inputs[relative].read_text(encoding="ascii")
    if text.count('GameRulesName == "HWMP 2.4.5 Cataclysm"') != 2:
        raise ValueError("Unknown base callback gates")
    write(
        source,
        relative,
        text.replace('GameRulesName == "HWMP 2.4.5 Cataclysm"', f'GameRulesName == "{RULE_NAME}"'),
    )

    inherited = stock_files()
    inherited.update(index(DONOR))
    from cataclysm import quote

    descriptions(source, design, inherited, quote, report_path=work / "descriptions.json")
    # Show the capacity grant in both build tooltips and the selected-unit description.
    from cataclysm_descriptions import description_ids
    from language_data import LANGUAGES

    ids = description_ids(design)
    for language in LANGUAGES:
        path = source / f"locale/{language}/hwmp24_cataclysm.ucs"
        text = path.read_bytes().decode("utf-16")
        for ident, grant in config["capacity_providers"].items():
            pattern = r"(?m)^(" + str(ids[ident]) + r"\t[^\r\n]+)(\r?)$"
            text, count = re.subn(
                pattern, lambda m, value=grant: m[1] + f" | +{value} SU" + m[2], text
            )
            if count != 1:
                raise ValueError("Missing provider unit description: " + ident)
        # Build descriptions use stable sorted IDs from the generator; append grants
        # using its native build-name table rather than a second ship-order assumption.
        locale = source / f"locale/{language}/hwmp24_cataclysm.lua"
        mapping = locale.read_text(encoding="ascii").split("HWMP_CataclysmBuildDescriptions =", 1)[
            1
        ]
        mapping = mapping.split("HWMP_CataclysmBuildTimedDescriptions =", 1)[0]
        build_ids = dict(re.findall(r'\["([^"]+)"\]="\$(\d+)"', mapping))
        for ident, grant in config["capacity_providers"].items():
            key = build_ids.get(ident)
            if key is not None:
                for number in (int(key), int(key) + 200):
                    pattern = r"(?m)^(" + str(number) + r"\t[^\r\n]+)(\r?)$"
                    text, count = re.subn(
                        pattern,
                        lambda m, value=grant: m[1] + f"\\n\\n+{value} SU" + m[2],
                        text,
                    )
                    if count != 1:
                        raise ValueError("Missing provider build description: " + ident)
        path.write_bytes(text.encode("utf-16"))

    for relative in ("ui/newui/background/logo.lua", "playerspatch_buildnumber.lua"):
        write(
            source,
            relative,
            inputs[relative].read_text(encoding="ascii").replace("2.4.5", "2.4.6 Test1"),
        )
    manifest = {name: sha(path) for name, path in index(source).items()}
    altered = sorted(name for name in manifest if before.get(name) != manifest[name])
    save(
        work / "manifest.json",
        {
            "base": config["base_content_revision"],
            "files": manifest,
            "changed_resources": altered,
        },
    )
    from verify_cataclysm246 import verify

    checked = verify(source, inputs, design, config)
    save(work / "verification-source.json", checked)
    release.mkdir()
    for language, name in (("", "README.md"), ("ru/", "README.ru.md")):
        text = (PROJECT / f"docs/{language}CATACLYSM_2_4_6_TEST.md").read_text(encoding="utf8")
        text = text.replace("ru/CATACLYSM_2_4_6_TEST.md", "README.ru.md").replace(
            "../CATACLYSM_2_4_6_TEST.md", "README.md"
        )
        (release / name).write_text(text, encoding="utf8", newline="\n")
    for language, name in (("", "SU_PRICES.md"), ("ru/", "SU_PRICES.ru.md")):
        original = (PROJECT / f"docs/{language}SUPPORT_UNITS_PRICES.md").read_text(encoding="utf8")
        lines = []
        for line in original.splitlines():
            match = re.match(r"\| (\w+) / `([^`]+)` \| ([^|]+) \|", line)
            if match:
                row = design["ships"][match[2]]
                line = f'| {match[1]} / `{match[2]}` | {match[3].strip()} | {row["su_per_hull"]} | {row["build_batch"]} | {row["su_per_group"]} |'
                lines.append(line)
        title = "# 2.4.6 Test1 SU prices" if not language else "# Цены SU — 2.4.6 Test1"
        table = "| Race / ID | Name | SU / hull | Batch | SU / entry |\n|---|---|---:|---:|---:|\n"
        (release / name).write_text(
            title + "\n\n" + table + "\n".join(lines) + "\n", encoding="utf8"
        )
    save(
        release / "candidate.json",
        {
            "version": config["version"],
            "base": config["base_content_revision"],
            "capacity": config,
            "source_checks": checked,
        },
    )
    result = {
        "version": config["version"],
        "work": str(work),
        "source": str(source),
        "release": str(release),
        "changed_resources": len(altered),
        "engine_tested": False,
        "installed": False,
        "published": False,
        "queue_reservations_certified": False,
    }
    if package:
        verified = package_source(source, release, "HWMPPatch246Test.big", TITLE)
        save(work / "verification-package.json", verified)
        result["main_sha256"] = sha(release / "HWMPPatch246Test.big")
        result["main_bytes"] = (release / "HWMPPatch246Test.big").stat().st_size
        result["full_extract_hash_comparison"] = True
        (release / "config.txt").write_text(
            f"Title: {TITLE}\n\nTags: Balance Fixes Multiplayer\nGameType: HomeworldRM\nModType: MOD\nBigFilename: HWMPPatch246Test.big\n\nDescription:\nUnpublished experimental dynamic SU capacity; native acceptance pending.\n",
            encoding="ascii",
        )
        # Keep packaging logs outside the distributable.
        for path in release.glob("*.log"):
            shutil.move(str(path), str(work / path.name))
        sums = {p.name: sha(p) for p in release.iterdir() if p.is_file()}
        (release / "SHA256SUMS.txt").write_text(
            "".join(f"{value}  {name}\n" for name, value in sorted(sums.items())),
            encoding="ascii",
        )
        archive = work / "HWMPPatch246Test.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipout:
            for path in release.iterdir():
                zipout.write(path, "HWMPPatch246Test/" + path.name)
        result["zip"] = str(archive)
    if {name: sha(path) for name, path in inputs.items()} != before:
        raise ValueError("Frozen published input was mutated")
    save(work / "prepared.json", result)
    save(PROJECT / "local/cataclysm246/latest.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.package), indent=2))
