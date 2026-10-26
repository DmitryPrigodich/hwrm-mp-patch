"""Compare pinned Hgn/Vgr economy data; passive Classic reader, no engine launch.

Research Lua is evaluated with file access removed and a strict data-only loader.
Lua4 table iteration is translated for inspection only; no runtime file is edited.
"""

import argparse
import json
from pathlib import Path
import re
from lupa.lua51 import LuaRuntime
from hwrm_common import CACHE, PROJECT, DONOR_SHA, ARCHIVE, index, save, sha
from hwrm_inspect import plain, record_config
from lua4_data import tables as classic_tables

VERSIONS = {
    "classic": ("classic",),
    "remastered": ("rm-base", "rm-hw1", "rm-hw2", "rm-mp"),
    "pp23": ("rm-base", "rm-hw1", "rm-hw2", "rm-mp", "regular"),
    "test21": ("rm-base", "rm-hw1", "rm-hw2", "rm-mp", "test"),
}
SHIP_IDS = tuple(
    r + "_" + s
    for r in ("hgn", "vgr")
    for s in ("resourcecollector", "resourcecontroller", "mothership", "carrier", "shipyard")
)
SUB_IDS = tuple(
    r + "_" + host + "_innate_resource" for r in ("hgn", "vgr") for host in ("ms", "c", "sy")
)
FIELDS = (
    "maxhealth",
    "regentime",
    "minRegenTime",
    "buildCost",
    "buildTime",
    "thrusterMaxSpeed",
    "mainEngineMaxSpeed",
    "thrusterAccelTime",
    "thrusterBrakeTime",
    "mainEngineAccelTime",
    "mainEngineBrakeTime",
    "rotationMaxSpeed",
    "rotationAccelTime",
    "slideMoveRange",
    "goalReachEpsilon",
    "holdSlots",
    "BuildFamily",
    "ArmourFamily",
    "AttackFamily",
    "DockFamily",
    "UnitCapsFamily",
    "UnitCapsShipType",
    "dockTimeBeforeStart",
    "dockTimeBetweenTwoFormations",
    "costToBuild",
    "timeToBuild",
    "inactiveTimeAfterDamage",
    "activateHealthPercentage",
    "innate",
)
PIN = PROJECT / "baseline/economy-inputs.json"
WORK = PROJECT / "local/economy-audit"


class Sources:
    def __init__(self):
        self.layers = {}
        self.used = {}
        self.resolution = {}
        for layer in dict.fromkeys(x for layers in VERSIONS.values() for x in layers):
            root = CACHE / "players-patch-audit" / layer
            if not root.is_dir():
                raise RuntimeError("Missing extracted input: " + str(root))
            self.layers[layer] = index(root)

    def effective(self, version):
        result = {}
        for layer in VERSIONS[version]:
            result.update({name: (layer, path) for name, path in self.layers[layer].items()})
        return result

    def use(self, version, relative):
        relative = relative.lower()
        layer, path = self.effective(version)[relative]
        key = layer + "/" + relative
        self.used[key] = sha(path)
        self.resolution[version + "/" + relative] = key
        return path, {"input": key, "sha256": self.used[key]}


def translate(text):
    return re.sub(
        r"\bfor\s+(\w+(?:\s*,\s*\w+)?)\s+in\s+([\w.]+)\s+do", r"for \1 in pairs(\2) do", text
    )


def data_table(sources, version, relative, name, research=False):
    path, proof = sources.use(version, relative)
    if version == "classic":
        values, _ = classic_tables(path)
        return values[name], proof
    vm = LuaRuntime(register_eval=False, register_builtins=False)
    g = vm.globals()
    for forbidden in (
        "python",
        "os",
        "io",
        "package",
        "require",
        "dofile",
        "loadfile",
        "debug",
        "loadstring",
    ):
        g[forbidden] = None
    g.getn = vm.eval("table.getn")
    active = set()

    def load(relative):
        if relative in active:
            raise ValueError("Recursive data include: " + relative)
        active.add(relative)
        path, _ = sources.use(version, relative)
        vm.execute(translate(path.read_text(encoding="utf-8-sig")))
        active.remove(relative)

    def scan(folder, pattern):
        assert folder.lower().startswith("data:"), folder
        relative = folder[5:].replace("\\", "/").lower().strip("/")
        if relative == "scripts/productiontimes":
            return  # UI annotation only; no gameplay table changes.
        assert research and relative.endswith("/scripts/research") and pattern == "*.lua", (
            folder,
            pattern,
        )
        names = [
            n
            for n in sources.effective(version)
            if n.startswith(relative + "/")
            and "/" not in n[len(relative) + 1 :]
            and n.endswith(".lua")
        ]
        assert names, folder
        for n in sorted(names):
            load(n)

    g.doscanpath = scan
    load(relative)
    return plain(g[name]), proof


def config(sources, version, relative):
    path, proof = sources.use(version, relative)
    if version == "classic":
        values, calls = classic_tables(path)
        configs = [v for k, v in values.items() if k in ("NewShipType", "NewSubSystemType")]
        assert len(configs) == 1, relative
        cfg = configs[0]
        calls = [(c["name"], c["args"][1:]) for c in calls]
    else:
        text = re.sub(
            r"StartSubSystemConfig\(\)", "StartShipConfig()", path.read_text(encoding="utf-8-sig")
        )
        cfg, calls = record_config(text)
    selected = {k: cfg[k] for k in FIELDS if k in cfg}
    retained = [
        (n, a)
        for n, a in calls
        if n
        in ("addAbility", "AddSubSystemMultiplier", "setSupplyValue", "StartShipHardPointConfig")
    ]
    return {"source": proof, "values": selected, "calls": retained}


def caps(sources, version, race):
    paths = (
        ["scripts/unitcaps/normal.lua"]
        if version == "classic"
        else [
            "scripts/rules/deathmatch/unitcaps/normal.lua",
            f"scripts/races/{race}/deathmatch/unitcaps/normal.lua",
        ]
    )
    result = {}
    for relative in paths:
        path, _ = sources.use(version, relative)
        if version == "classic":
            _, calls = classic_tables(path)
            result.update(
                {
                    c["args"][0]: c["args"][1]
                    for c in calls
                    if c["name"] in ("UC_Family", "UC_ShipType")
                }
            )
            result.update(
                {
                    c["args"][1]: c["args"][2]
                    for c in calls
                    if c["name"] in ("UC_FamilyOverride", "UC_ShipTypeOverride")
                    and c["args"][0].lower() == race
                }
            )
        else:
            # This input subset consists of literal, top-level cap declarations.
            result.update(
                {
                    name: float(value)
                    for name, value in re.findall(
                        r'^\s*supplyLimit\("([^"\n]+)"\s*,\s*([\d.]+)\)', path.read_text(), re.M
                    )
                }
            )
    return {
        k: result[k]
        for k in ("Resource", "ResourceCollector", "ResourceController", "Utility")
        if k in result
    }


def audit(pin_inputs=False):
    assert sha(ARCHIVE) == DONOR_SHA, "Pinned Test21 archive differs."
    sources = Sources()
    report = {
        "native_engine_tested": False,
        "runtime_changed": False,
        "assumptions": [
            "ordinary human game; no scenario property overrides",
            "normal limits and default starting-fleet suffix",
            "AI, crate grants and all-research modes excluded from human income comparisons",
        ],
        "versions": {},
    }
    for version in VERSIONS:
        entry = {
            "ships": {},
            "receivers": {},
            "fleets": {},
            "caps": {},
            "economic_research": {},
            "collector_animation_inputs": {},
            "receiver_geometry_inputs": {},
        }
        for ident in SHIP_IDS:
            entry["ships"][ident] = config(sources, version, f"ship/{ident}/{ident}.ship")
        for ident in SUB_IDS:
            entry["receivers"][ident] = config(sources, version, f"subsystem/{ident}/{ident}.subs")
        for race in ("hiigaran", "vaygr"):
            fleet, proof = data_table(
                sources, version, f"scripts/startingfleets/{race}00.lua", "PersistantData"
            )
            entry["fleets"][race] = {
                "source": proof,
                "squadrons": list(fleet["Squadrons"].values()),
            }
            entry["caps"][race] = caps(sources, version, race)
            relative = (
                f"scripts/building and research/{race}/research.lua"
                if version == "classic"
                else f"scripts/races/{race}/scripts/def_research.lua"
            )
            research, _ = data_table(sources, version, relative, "research", research=True)
            names = set()
            for row in research.values():
                assert row["Name"] not in names, (version, race, row["Name"])
                names.add(row["Name"])
            selected = [
                row
                for row in research.values()
                if "resource" in str(row.get("TargetName", "")).lower()
                or row.get("TargetName", "").lower() == "utility"
                or "ResourceCollection" in row.get("UpgradeName", "")
            ]
            entry["economic_research"][race] = sorted(selected, key=lambda r: r["Name"])
        for ident in ("hgn_resourcecollector", "vgr_resourcecollector"):
            parts = {}
            for ext in ("hod", "mad", "madstate", "events"):
                _, parts[ext] = sources.use(version, f"ship/{ident}/{ident}.{ext}")
            entry["collector_animation_inputs"][ident] = parts
        for ident in SHIP_IDS:
            if "resourcecollector" in ident:
                continue
            parts = {}
            for ext in ("hod", "mad", "madstate", "events"):
                relative = f"ship/{ident}/{ident}.{ext}"
                if relative in sources.effective(version):
                    _, parts[ext] = sources.use(version, relative)
            entry["receiver_geometry_inputs"][ident] = parts
        report["versions"][version] = entry
    inputs = {
        "schema": 1,
        "test21_archive_sha256": DONOR_SHA,
        "layers": VERSIONS,
        "files": dict(sorted(sources.used.items())),
        "mp_overlay": {n: sha(p) for n, p in sources.layers["rm-mp"].items()},
        "resolution": dict(sorted(sources.resolution.items())),
    }
    # JSON normalizes tuples; compare the exact same portable representation.
    inputs = json.loads(json.dumps(inputs))
    if pin_inputs:
        if PIN.exists():
            raise RuntimeError("Input pin already exists; inspect changes before replacing it.")
        save(PIN, inputs)
    assert (
        PIN.exists() and json.loads(PIN.read_text(encoding="utf8")) == inputs
    ), "Economic inputs or layer resolution changed."
    report["input_files"] = len(sources.used)
    report["pin_sha256"] = sha(PIN)
    report["checks"] = verify_findings(report)
    save(WORK / "audit.json", report)
    print(
        json.dumps(
            {
                "report": str(WORK / "audit.json"),
                "input_files": len(sources.used),
                "checks": report["checks"],
                "native_engine_tested": False,
            }
        )
    )
    return report


def ability(record, name):
    return next(a for n, a in record["calls"] if n == "addAbility" and a[0] == name)


def verify_findings(report):
    versions = report["versions"]
    for version in versions.values():
        for race in ("hgn", "vgr"):
            assert ability(version["ships"][race + "_resourcecollector"], "Harvest")[3] == 8
            assert ability(version["ships"][race + "_resourcecontroller"], "ShipHold")[2] == 40
            assert ability(version["ships"][race + "_mothership"], "ShipHold")[2] == 250
            for host in ("carrier", "shipyard"):
                assert ability(version["ships"][race + "_" + host], "ShipHold")[2] == 40
    test = versions["test21"]
    rm = versions["remastered"]
    for race, expected in (("hiigaran", 6), ("vaygr", 7)):
        for version in ("remastered", "pp23", "test21"):
            fleet = versions[version]["fleets"][race]["squadrons"]
            assert (
                next(s.get("number", 1) for s in fleet if "resourcecollector" in s["type"].lower())
                == expected
            )
    assert ability(rm["ships"]["vgr_resourcecollector"], "Harvest")[2] == 208
    for race in ("hgn", "vgr"):
        assert ability(test["ships"][race + "_resourcecollector"], "Harvest")[2] == 200
        assert test["ships"][race + "_resourcecontroller"]["values"]["buildCost"] == 1000
        assert test["ships"][race + "_resourcecontroller"]["values"]["buildTime"] == 45
        assert (
            test["collector_animation_inputs"][race + "_resourcecollector"]
            == rm["collector_animation_inputs"][race + "_resourcecollector"]
        )
    for ident in test["receiver_geometry_inputs"]:
        assert {k: v["sha256"] for k, v in test["receiver_geometry_inputs"][ident].items()} == {
            k: v["sha256"] for k, v in rm["receiver_geometry_inputs"][ident].items()
        }, ident
    assert versions["classic"]["caps"]["hiigaran"]["ResourceCollector"] == 20
    for receiver in test["receivers"].values():
        vals = receiver["values"]
        assert (
            vals["inactiveTimeAfterDamage"],
            vals["activateHealthPercentage"],
            vals["regentime"],
        ) == (60, 0.05, 180)
    for race in ("hiigaran", "vaygr"):
        assert (
            test["caps"][race]["Resource"] == 24 and test["caps"][race]["ResourceCollector"] == 22
        )
        for row in test["economic_research"][race]:
            if row.get("UpgradeName") == "ResourceCollectionRate":
                assert row.get("AIOnly") == 1 and row.get("DoNotGrant") == 1
    return [
        "Harvest and dropoff parameters recorded for four effective versions",
        "stock six/seven fleet and collector animation inheritance verified",
        "Test controller price/time and all six receiver recovery fields verified",
        "shared resource cap and AI-only rate upgrades separated",
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pin-inputs", action="store_true")
    args = parser.parse_args()
    audit(args.pin_inputs)
