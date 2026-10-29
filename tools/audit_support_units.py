"""Read-only SU feasibility audit. No build, package, installation or engine launch.

Reads effective HWMP ship/build/cap definitions with the existing passive Lua
inspector. Defaults are source configuration, not observed hull counts or combat
results. Screenshot price mappings remain draft; the hull|group notation is user-confirmed.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--sketch", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    sketch_path = args.sketch or project / "research/support-units/sketch.json"
    output = args.output or project / "local/support-units-research"
    output.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(project / "tools"))
    from hwrm_common import CACHE, GAME
    from hwrm_inspect import record_config
    from production_data import effective_files, table

    files = effective_files()
    used = {}

    def source(name):
        path = files[name.lower()]
        # Stable logical path and source hash; no user/game/profile paths in report.
        layer = "override" if path.is_relative_to(project) else "native-cache"
        if path.is_relative_to(CACHE):
            layer = path.relative_to(CACHE).as_posix()
        used[name.lower()] = {"source": layer, "sha256": digest(path)}
        return path

    sketch = json.loads(sketch_path.read_text(encoding="utf-8"))
    raw_rows = [
        dict(zip(sketch["columns"], row), race=race)
        for race, rows in sketch["races"].items()
        for row in rows
    ]
    lookup = {
        row["candidate_stock_id"]: row for row in raw_rows if row["candidate_stock_id"] is not None
    }
    assert len(lookup) == sum(row["candidate_stock_id"] is not None for row in raw_rows)
    ships = {}
    races = {}
    for race in ("hiigaran", "vaygr", "kushan", "taiidan"):
        builds = table(source(f"scripts/races/{race}/scripts/def_build.lua"), "build")
        ids = sorted({row["ThingToBuild"].lower() for row in builds.values() if row["Type"] == 0})
        cap_paths = [
            "scripts/rules/deathmatch/unitcaps/normal.lua",
            f"scripts/races/{race}/deathmatch/unitcaps/normal.lua",
        ]
        caps = {}
        for relative in cap_paths:
            text = source(relative).read_text(encoding="utf-8-sig")
            caps.update(
                {
                    key: float(value)
                    for key, value in re.findall(
                        r'^\s*supplyLimit\("([^"]+)"\s*,\s*([\d.]+)\)', text, re.M
                    )
                }
            )
        missing_weights = []
        for ident in ids:
            relative = f"ship/{ident}/{ident}.ship"
            text = source(relative).read_text(encoding="utf-8-sig")
            cfg, calls = record_config(text)
            supplies = {a[0]: a[1] for name, a in calls if name == "setSupplyValue"}
            fields = (
                "displayedName",
                "buildCost",
                "buildTime",
                "SquadronSize",
                "buildBatch",
                "BuildFamily",
                "DisplayFamily",
                "addedUnitCaps",
            )
            row = {
                "definition": relative,
                "source_defaults": {k: cfg[k] for k in fields if k in cfg},
                "supply": supplies,
            }
            if ident in lookup:
                entry = lookup[ident]
                parts = list(map(int, entry["literal_su"].split("|")))
                assert all(value >= 0 for value in parts)
                row["tentative_sketch"] = entry
                row["tentative_su_per_hull"] = parts[0]
                if len(parts) == 2:
                    assert parts[0] > 0 and parts[1] % parts[0] == 0
                    row["sketch_implied_group_hulls"] = parts[1] // parts[0]
                    row["matches_explicit_buildBatch"] = (
                        cfg.get("buildBatch") == row["sketch_implied_group_hulls"]
                    )
            else:
                missing_weights.append(ident)
            ships[ident] = row
        # Mothership is generally a starting asset, not a production-table entry.
        start_relative = f"ship/{'hgn' if race == 'hiigaran' else 'vgr' if race == 'vaygr' else 'kus' if race == 'kushan' else 'tai'}_mothership/"
        start_id = start_relative.rstrip("/").split("/")[-1]
        source(start_relative + start_id + ".ship")
        races[race] = {
            "build_table_ship_types": ids,
            "normal_caps": caps,
            "unpriced_build_types": missing_weights,
            "unpriced_starting_assets": [start_id],
        }

    native_symbols = []
    exe = GAME / "HomeworldRM/Bin/Release/HomeworldRM.exe"
    exe_hash = None
    if exe.exists():
        content = exe.read_bytes()
        exe_hash = hashlib.sha256(content).hexdigest()
        symbols = (
            "setSupplyValue",
            "supplyLimit",
            "supplyShow",
            "supplyDesc",
            "supplyIndent",
            "GetUnitCapFamilyId",
            "GetUnitCapForFamily",
            "GetUnitCapMaxForFamily",
            "Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping",
            "SobGroup_Count",
            "getRulesNum",
            "doRulesHaveTag",
            "addedUnitCaps",
            "SobGroup_GetActualSquadronSize",
        )
        native_symbols = {symbol: (symbol.encode("ascii") + b"\0") in content for symbol in symbols}
    for relative in (
        "scripts/familylist.lua",
        "ui/newui/unitcapinfopopup.lua",
        "ai/default/cpubuildsubsystem.lua",
    ):
        source(relative)
    fixes = json.loads((project / "hwmp-patch-2.4/fixes.json").read_text(encoding="utf-8"))
    report = {
        "schema": 1,
        "date": "2026-10-27",
        "native_engine_tested": False,
        "runtime_changed": False,
        "scope": "ordinary original-race deathmatch; source defaults only",
        "owner_commit": subprocess.check_output(
            ["git", "-C", str(project), "rev-parse", "HEAD"], text=True
        ).strip(),
        "fix_revision": fixes["fix_revision"],
        "donor_sha256": fixes["base_sha256"],
        "sketch_sha256": digest(sketch_path),
        "exe_sha256": exe_hash,
        "symbol_presence_only_not_api_scope_proof": native_symbols,
        "sketch_row_count": len(raw_rows),
        "unmapped_sketch_rows": [row for row in raw_rows if not row["candidate_stock_id"]],
        "mapped_candidates_not_buildable": sorted(set(lookup) - set(ships)),
        "races": races,
        "ships": ships,
        "inputs": used,
    }
    (output / "audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Support Units: source audit",
        "",
        "Source defaults; tentative screenshot mappings; no engine test.",
        "",
        "| Type | Cost RU | Seconds | Explicit size / batch | Supply assignments | Sketch SU |",
        "|---|---:|---:|---|---|---|",
    ]
    for ident, row in sorted(ships.items()):
        c = row["source_defaults"]
        supply = ", ".join(f"{k}={v:g}" for k, v in row["supply"].items())
        su = row.get("tentative_sketch", {}).get("literal_su", "UNPRICED").replace("|", " / ")
        lines.append(
            f"| {ident} | {c.get('buildCost', '?')} | {c.get('buildTime', '?')} | "
            f"{c.get('SquadronSize', 'unset')} / {c.get('buildBatch', 'unset')} | {supply} | {su} |"
        )
    lines += [
        "",
        "Missing weights must not default to zero. Motherships also need an explicit policy.",
        "",
    ]
    (output / "catalog.md").write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "sketch_rows": len(raw_rows),
                "production_ship_types": len(ships),
                "hashed_inputs": len(used),
                "missing_by_race": {r: len(v["unpriced_build_types"]) for r, v in races.items()},
                "mapped_candidates_not_buildable": report["mapped_candidates_not_buildable"],
                "native_engine_tested": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
