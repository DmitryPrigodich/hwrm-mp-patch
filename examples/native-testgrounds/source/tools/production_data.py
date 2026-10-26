"""Inspect native production/resource data; generate tooltip times, not game stats."""

import json
from pathlib import Path
import re
from lupa.lua51 import LuaRuntime
from hwrm_common import PROJECT, CACHE, DONOR, index, sha, save
from hwrm_inspect import record_config, plain

RACES = ("hiigaran", "vaygr", "kushan", "taiidan")
STOCK = ("rm-base", "rm-hw2", "rm-hw1")
CAMPAIGNS = ("rm-campaign-hw1", "rm-campaign-hw2")
PIN = PROJECT / "baseline/native-production-inputs.json"
ROOT = PROJECT / "hwmp-patch-2.4"
WORK = PROJECT / "local/data-audit"


def stock_files(campaigns=False):
    result = {}
    for folder in STOCK + (CAMPAIGNS if campaigns else ()):
        source = CACHE / "players-patch-audit" / folder
        if not source.is_dir():
            raise RuntimeError("Run tools/prepare_inputs.py; missing stock input: " + folder)
        result.update(index(source))
    return result


def effective_files(source=None, campaigns=False):
    result = stock_files(campaigns)
    result.update(index(DONOR))
    result.update(index(Path(source) if source else ROOT / "overrides"))
    return result


def table(path, name):
    vm = LuaRuntime(register_eval=False, register_builtins=False)
    for key in ("python", "os", "io", "package", "require", "dofile", "loadfile", "debug"):
        vm.globals()[key] = None
    vm.globals().doscanpath = lambda *args: None
    vm.execute(path.read_text(encoding="utf-8-sig"))
    return plain(vm.globals()[name])


def config(path):
    text = path.read_text(encoding="utf-8-sig")
    # Passive recorder gives each config constructor the same inert data table.
    text = re.sub(r"Start\w+Config\(\)", "StartShipConfig()", text)
    return record_config(text)[0]


def catalog(source=None, check_pins=True):
    files = effective_files(source)
    native = stock_files()
    rows = []
    inputs = {}
    values = {}
    for race in RACES:
        build = table(files[f"scripts/races/{race}/scripts/def_build.lua"], "build")
        for _, item in sorted(build.items()):
            name = item["ThingToBuild"]
            ident = name.lower()
            kind, suffix, field = (
                ("ship", "ship", "buildTime")
                if item["Type"] == 0
                else ("subsystem", "subs", "timeToBuild")
            )
            relative = f"{kind}/{ident}/{ident}.{suffix}"
            path = files.get(relative)
            if path is None:
                raise RuntimeError("Missing production definition: " + relative)
            data = config(path)
            seconds = data.get(field)
            assert (
                isinstance(seconds, (int, float)) and not isinstance(seconds, bool) and seconds >= 0
            ), (name, seconds)
            if path == native.get(relative):
                inputs[relative] = {
                    "cache_path": path.relative_to(CACHE).as_posix(),
                    "sha256": sha(path),
                }
            assert name not in values or values[name] == seconds, ("Conflicting build time", name)
            values[name] = seconds
            rows.append(
                {
                    "race": race,
                    "name": name,
                    "seconds": seconds,
                    "definition": relative,
                    "description": item.get("Description"),
                    "visible": data.get("visible"),
                    "field": field,
                }
            )
    if check_pins:
        expected = json.loads(PIN.read_text(encoding="utf8"))["files"]
        assert (
            inputs == expected
        ), "Inherited production inputs changed; review the native input manifest."
    return rows, values, inputs


def time_lua(values):
    return (
        "-- HWMP2.4: generated from effective ship/subsystem base times by production_data.py.\n-- Native production/research bonuses are not applied to these tooltip values.\nbuildtimes = {\n"
        + "".join(
            "[" + json.dumps(name) + "] = " + json.dumps(format(seconds, "g")) + ",\n"
            for name, seconds in sorted(values.items())
        )
        + "}\n"
    )


def generate():
    rows, values, _ = catalog()
    target = ROOT / "overrides/scripts/productiontimes/buildtimes.lua"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(time_lua(values), encoding="ascii", newline="\n")
    for number in range(5):
        relative = f"resource/asteroid/asteroid{number}/asteroid{number}.resource"
        text = (DONOR / relative).read_text(encoding="ascii")
        for field, value in (("displayedName", "2506"), ("sobDescription", "2507")):
            old = f'NewResourceType.{field}="{value}"'
            new = f'NewResourceType.{field}="${value}"'
            assert text.count(old) == 1, (relative, field)
            text = text.replace(old, new, 1)
        target = ROOT / "overrides" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="ascii", newline="\n")
    return {
        "production_rows": len(rows),
        "unique_build_targets": len(values),
        "resource_label_definitions": 5,
    }


STRINGS = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
COMMENTS_AND_STRINGS = re.compile(STRINGS + r"|--\[\[.*?\]\]|--[^\n]*", re.S)


def uncomment(text):
    return COMMENTS_AND_STRINGS.sub(
        lambda m: "\n" * m[0].count("\n") if m[0].startswith("--") else m[0], text
    )


def resource_usage(source=None):
    files = effective_files(source, campaigns=True)
    sites = {}
    dynamic = []
    scanned = 0
    quoted_zero = []
    for name, path in sorted(files.items()):
        if not name.startswith(("leveldata/", "scripts/")) or path.suffix not in (".lua", ".level"):
            continue
        scanned += 1
        text = uncomment(path.read_text(encoding="utf8", errors="replace"))
        masked = re.sub(STRINGS, lambda m: " " * len(m[0]), text)
        for match in re.finditer(r"\baddAsteroid\s*\(", masked):
            line = text.count("\n", 0, match.start()) + 1
            literal = re.match(r'\s*["\']([^"\']+)["\']', text[match.end() :])
            if literal:
                sites.setdefault(literal[1].lower(), []).append({"path": name, "line": line})
            else:
                dynamic.append({"path": name, "line": line})
        if re.search(r'["\']asteroid0["\']', text, re.I):
            quoted_zero.append(name)
    usage = {}
    for ident, rows in sorted(sites.items()):
        paths = sorted({row["path"] for row in rows})
        usage[ident] = {
            "literal_call_sites": len(rows),
            "files": paths,
            "multiplayer_files": [p for p in paths if p.startswith("leveldata/multiplayer/")],
            "examples": rows[:2],
        }
    return {
        "scanned_files": scanned,
        "usage": usage,
        "dynamic_call_sites": dynamic,
        "quoted_asteroid0_files": quoted_zero,
        "method": "Comment/string-aware static call sites, not executed maps or physical asteroid counts.",
    }


def verify(source):
    files = effective_files(source)
    rows, expected, _ = catalog(source)
    actual = table(files["scripts/productiontimes/buildtimes.lua"], "buildtimes")
    assert actual == {
        name: format(value, "g") for name, value in expected.items()
    }, "Tooltip time table is stale."
    resource_fields = {}
    for number in range(5):
        relative = f"resource/asteroid/asteroid{number}/asteroid{number}.resource"
        old = config(DONOR / relative)
        new = config(files[relative])
        expected_resource = dict(old, displayedName="$2506", sobDescription="$2507")
        assert new == expected_resource, ("Resource gameplay fields changed", relative)
        resource_fields["asteroid" + str(number)] = {
            "resourceValue": new.get("resourceValue"),
            "maxVelocity": new.get("maxVelocity"),
        }
    return {
        "production_rows": len(rows),
        "unique_build_targets": len(expected),
        "all_times_match_definitions": True,
        "resource_labels_fixed": 5,
        "resource_gameplay_fields_unchanged": True,
        "preserved_resource_values": resource_fields,
    }


def audit(source=None):
    rows, values, inputs = catalog(source)
    upstream = table(DONOR / "scripts/productiontimes/buildtimes.lua", "buildtimes")
    files = effective_files(source)
    old_errors = []
    for name, shown in upstream.items():
        assert name in values, ("Uncatalogued upstream time", name)
        if float(shown) != values[name]:
            old_errors.append({"name": name, "shown": shown, "actual": values[name]})
    missing = [row for row in rows if row["name"] not in upstream]
    before_resources = []
    native = stock_files()
    for number in range(5):
        relative = f"resource/asteroid/asteroid{number}/asteroid{number}.resource"
        old = config(native[relative])
        patch = config(DONOR / relative)
        changes = {
            key: {"stock": old.get(key), "test21": patch.get(key)}
            for key in ("displayedName", "sobDescription", "resourceValue", "maxVelocity")
            if old.get(key) != patch.get(key)
        }
        before_resources.append({"name": "asteroid" + str(number), "changes": changes})
    report = {
        "engine_tested": False,
        "game_launched": False,
        "construction_rows": len(rows),
        "unique_targets": len(values),
        "original_time_entries": len(upstream),
        "original_incorrect_values": old_errors,
        "original_missing_rows": missing,
        "original_missing_unique_targets": len({row["name"] for row in missing}),
        "native_input_files": len(inputs),
        "resources_vs_stock": before_resources,
        "resource_usage": resource_usage(source),
    }
    if source:
        report["verification"] = verify(source)
    save(WORK / "audit.json", report)
    print(
        json.dumps(
            {
                "construction_rows": len(rows),
                "original_time_entries": len(upstream),
                "incorrect_values": len(old_errors),
                "missing_rows": len(missing),
                "missing_unique": report["original_missing_unique_targets"],
                "scanned_resource_files": report["resource_usage"]["scanned_files"],
                "asteroid0": report["resource_usage"]["usage"].get("asteroid0"),
                "engine_tested": False,
            }
        )
    )
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    audit(args.source)
