"""Isolated native accounting probes. Preparation and collection never auto-launch."""

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess

from auto_testgrounds import lua
from cataclysm import model
from hwrm_common import CACHE, GAME, PROJECT, index, save, sha
from hwrm_archive import package_source
import su_boundary_tests as boundary

COUNTS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 32, 64, 65, 128]
QWEIGHTS = [1 / 64, 0.25, 0.46875, 0.5, 0.53125, 0.625, 0.75, 1, 1.25, 1.5, 2.34375]


def prepare(scale):
    assert scale in (32, 64)
    previous = boundary.prepared()
    original = previous
    seen = set()
    while original.get("experimental_scale") is not None or original.get("caps_probe_only"):
        assert original["work"] not in seen, "Experimental baseline cycle"
        seen.add(original["work"])
        previous_work = json.loads((Path(original["work"]) / "previous-latest.json").read_text())[
            "work"
        ]
        original = json.loads((Path(previous_work) / "prepared.json").read_text(encoding="utf8"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    work = boundary.WORK / ("accounting" + str(scale) + "-" + stamp)
    source = work / "source"
    work.mkdir(parents=True)
    shutil.copytree(original["source"], source)
    token = "scale" + str(scale) + "_" + stamp
    design = model()
    frozen_hud = (Path(original["source"]) / "scripts/hwmp24/cataclysm_hud.lua").read_text(
        encoding="ascii"
    )
    frozen = re.search(r"HWMP_CataclysmBudgets = \{([^}]+)\}", frozen_hud)
    assert frozen, "Historical accounting source has no budget table"
    design["budgets"] = {name: int(value) for name, value in re.findall(r"(\w+)=(\d+)", frozen[1])}
    frozen_costs = dict(
        (name, int(value)) for name, value in re.findall(r'\["([^"\n]+)"\] = (\d+)', frozen_hud)
    )
    assert frozen_costs == {
        name: row["su_per_group"] for name, row in design["ships"].items()
    }, "Historical accounting prices differ; prepare a new independent baseline"
    altered = set()

    def put(name, text):
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="ascii", newline="\n")
        altered.add(name)

    for ident, row in design["ships"].items():
        relative = f"ship/{ident}/{ident}.ship"
        text = (source / relative).read_text(encoding="ascii")
        text, n = re.subn(
            r'(setSupplyValue\(NewShipType, "HWMP_SupportUnits", )[^)]+',
            lambda m: m[1] + format(row["su_per_group"] / scale, ".10g"),
            text,
        )
        assert n == 1
        if ident == "hgn_probe":
            text += f'\nif HWMP_CataclysmShip then setSupplyValue(NewShipType,"HWMP_SUQuantum",{1/scale:.10g}) end\n'
        if ident in (
            "hgn_probe",
            "hgn_battlecruiser",
            "hgn_destroyer",
            "hgn_defensefieldfrigate",
            "hgn_ioncannonfrigate",
            "hgn_resourcecollector",
        ):
            text += f'\nprint("HWMP_SUACC_SHIP|token={token}|id={ident}|cost={row["su_per_group"]/scale:.10g}|cat="..tostring(HWMP_CataclysmShip))\n'
        put(relative, text)
    for profile, budget in design["budgets"].items():
        assert budget / scale < 250
        relative = f"scripts/rules/hwmpcataclysm/unitcaps/{profile}.lua"
        text = (source / relative).read_text(encoding="ascii")
        text, n = re.subn(
            r'(supplyLimit\("HWMP_SupportUnits", )[^)]+',
            lambda m: m[1] + format(budget / scale, ".10g"),
            text,
        )
        assert n == 1
        put(
            relative,
            text + '\nsupplyLimit("HWMP_SUQuantum",250)\nsupplyShow("HWMP_SUQuantum","Never")\n',
        )
    relative = "scripts/familylist.lua"
    text = (source / relative).read_text(encoding="ascii")
    needle = "unitcapsFamily =\n{"
    assert text.count(needle) == 1
    put(
        relative,
        text.replace(
            needle,
            needle
            + '\n    {name="HWMP_SUQuantum",numParam=999,stringParam="SU accounting probe"},',
        ),
    )

    def query(world, case, phase="STEP"):
        tag = f"HWMP_SUACC|token={token}|world={world}|event=native|case={case}|step={phase}"
        code = (
            'local f=GetUnitCapFamilyId("HWMP_SupportUnits"); local q=GetUnitCapFamilyId("HWMP_SUQuantum"); '
            f'print("{tag}|family="..f.."|quantum_family="..q.."|used="..tostring(GetUnitCapForFamily(f)).."|max="..tostring(GetUnitCapMaxForFamily(f))..'
            '"|quantum="..tostring(GetUnitCapForFamily(q)).."|can="..CanBuild(HGN_INTERCEPTOR));'
        )
        return code

    # A guarded request does not deliberately bypass a negative admission result.
    relative = "scripts/hwmp24/su_boundary.lua"
    text = (source / relative).read_text(encoding="ascii")
    text = text.replace('"HWMP_SUB|world="', f'"HWMP_SUB|token={token}|world="')
    text = text.replace("HWMP_SUB_AI|case=", f"HWMP_SUB_AI|token={token}|case=")
    old = "                for j=1,c.requests do code=code..'Build('..SUB_ItemID..'); ' end"
    new = "                for j=1,c.requests do code=code..'if CanBuild('..SUB_ItemID..')==1 then Build('..SUB_ItemID..') end; ' end"
    assert text.count(old) == 1
    text = text.replace(old, new)
    needle = "                CPU_DoString(c.player,code)"
    prefix = query("Hgn_Auto", "CASE", "admission")
    text = text.replace(
        needle,
        "                local capQuery=gsub("
        + lua(prefix)
        + ',"CASE",c.id)\n                CPU_DoString(c.player,capQuery)\n'
        + needle,
    )
    put(relative, text)
    put(
        "scripts/hwmp24/su_accounting.lua",
        (PROJECT / "autotests/su_accounting.lua").read_text(encoding="ascii"),
    )

    measure = [
        dict(
            id=name,
            player=i + 1,
            ship="hgn_" + ship,
            cost=design["ships"]["hgn_" + ship]["su_per_group"],
            unbounded=int(name == "Probe"),
        )
        for i, (name, ship) in enumerate(
            [
                ("Battlecruiser", "battlecruiser"),
                ("Destroyer", "destroyer"),
                ("FieldFrigate", "defensefieldfrigate"),
                ("IonFrigate", "ioncannonfrigate"),
                ("Collector", "resourcecollector"),
                ("Interceptor", "interceptor"),
                ("Probe", "probe"),
            ]
        )
    ]
    plans = [
        (
            "Original",
            [
                ("battlecruiser", 11),
                ("destroyer", 1),
                ("defensefieldfrigate", 3),
                ("ioncannonfrigate", 1),
            ],
        ),
        (
            "MoreFields",
            [("battlecruiser", 11), ("defensefieldfrigate", 7), ("ioncannonfrigate", 1)],
        ),
        ("Destroyers", [("destroyer", 22), ("ioncannonfrigate", 3)]),
        (
            "Fields",
            [
                ("defensefieldfrigate", 89),
                ("ioncannonfrigate", 1),
                ("minelayercorvette", 1),
                ("resourcecollector", 1),
            ],
        ),
        ("Ions", [("ioncannonfrigate", 119), ("resourcecollector", 5)]),
        (
            "Mixed",
            [
                ("battlecruiser", 10),
                ("destroyer", 3),
                ("defensefieldfrigate", 1),
                ("minelayercorvette", 5),
                ("ioncannonfrigate", 1),
            ],
        ),
        (
            "ReverseOriginal",
            [
                ("ioncannonfrigate", 1),
                ("defensefieldfrigate", 3),
                ("destroyer", 1),
                ("battlecruiser", 11),
            ],
        ),
    ]
    equal = []
    for i, (name, parts) in enumerate(plans):
        plan = ["hgn_" + ship for ship, n in parts for _ in range(n)]
        assert sum(design["ships"][s]["su_per_group"] for s in plan) == 1805
        equal.append(dict(id=name, player=i + 1, plan=plan, inventory=dict(Counter(plan))))
    equal_nominal = design["budgets"]["normal"] - design["ships"]["hgn_interceptor"]["su_per_group"]
    adjustment = equal_nominal - 1885
    if adjustment < 0:
        raise ValueError("Equal-composition fixture requires at least1900 Normal SU")
    extra = boundary.padding(
        adjustment,
        [
            ("hgn_defensefieldfrigate", 20),
            ("hgn_resourcecollector", 4),
            ("hgn_minelayercorvette", 6),
            ("hgn_ioncannonfrigate", 15),
        ],
    )
    for case in equal:
        case["plan"].extend(extra)
        case["inventory"] = dict(Counter(case["plan"]))
        assert (
            80 + sum(design["ships"][ship]["su_per_group"] for ship in case["plan"])
            == equal_nominal
        )
    campaign_path = f"leveldata/campaign/{boundary.CAMPAIGN}.campaign"
    quantum = []
    probe_original = (Path(original["source"]) / "ship/hgn_probe/hgn_probe.ship").read_text(
        encoding="ascii"
    )
    assert probe_original.count("LoadModel(NewShipType,1);") == 1
    for number, weight in enumerate(QWEIGHTS):
        ident = f"hwmpsuq{number}"
        clone = probe_original.replace(
            "LoadModel(NewShipType,1);", 'LoadSharedModel(NewShipType,"hgn_probe");'
        )
        clone += f'\nif HWMP_CataclysmShip then setSupplyValue(NewShipType,"HWMP_SUQuantum",{weight}) end\nprint("HWMP_SUACC_SHIP|token={token}|id={ident}|weight={weight}|cat="..tostring(HWMP_CataclysmShip))\n'
        put(f"ship/{ident}/{ident}.ship", clone)
        quantum.append(
            dict(
                id=f"Weight{number}",
                player=number % 7 + 1,
                ship=ident,
                cost=0,
                unbounded=1,
                quantum_weight=weight,
            )
        )
    campaign = (source / campaign_path).read_text(encoding="ascii")
    worlds = dict(original["worlds"])
    for offset, (name, mode, cases) in enumerate(
        [
            ("Measure", "measure", measure),
            ("Equal", "equal", equal),
            ("EqualBuild", "equalbuild", equal),
            ("QuantumLow", "measure", quantum[:7]),
            ("QuantumHigh", "measure", quantum[7:]),
        ],
        53,
    ):
        world = "Hgn_" + name
        cases = deepcopy(cases)
        for c in cases:
            c["query"] = query(world, c["id"])
        lines = ["function DetermChunk()"]
        for p in range(8):
            x = p * 40000 - 100000
            for suffix, ship, z, dx in [
                ("Mother", "mothership", 9000, 0),
                ("CarrierA", "carrier", 0, 0),
                ("CarrierB", "carrier", 0, 2500),
            ]:
                if p == 0 and suffix != "Mother":
                    continue
                group = f"SUB_Mother{p}" if suffix == "Mother" else f"SUB_Carrier{p}" + suffix[-1]
                lines.extend(
                    [
                        f'addSquadron("{group}","hgn_{ship}",{{{x+dx},0,{z}}},{p},{{0,0,0}},1,0)',
                        f'createSOBGroup("{group}")',
                        f'addToSOBGroup("{group}","{group}")',
                    ]
                )
            lines.append(f'addSphere("SUB_Volume{p}",{{{x},0,40000}},15000)')
        lines += [
            'addCamera("SUB_Home",{-98750,0,0},{-93500,5500,-7000})',
            "setWorldBoundsInner({0,0,0},{300000,100000,300000})",
            "end",
            "function NonDetermChunk()",
            'loadBackground("m01")',
            "setSensorsManagerCameraDistances(100,1000000)",
            "end",
            "maxPlayers=8",
            f'levelDesc="{world}"',
            "player={}",
        ]
        lines += [
            f'player[{p}]={{id={p},name="",resources=100000,raceName="Hiigaran",startPos=0}}'
            for p in range(8)
        ]
        folder = f"leveldata/campaign/{boundary.CAMPAIGN}/{world}/{world}"
        put(folder + ".level", "\n".join(lines) + "\n")
        put(
            folder + ".lua",
            f'SUA_Token={lua(token)}\nSUA_World={lua(world)}\nSUA_Mode={lua(mode)}\nSUA_Scale={scale}\nSUA_EqualNominal={equal_nominal}\nSUA_Counts={lua([0,1,2,3,4,8,16,32,64] if name.startswith("Quantum") else COUNTS)}\nSUA_Cases={lua(cases)}\ndofilepath("data:scripts/hwmp24/su_accounting.lua")\ndofilepath("data:scripts/rules/hwmpcataclysm.lua")\n',
        )
        campaign += f'\nMission[{offset}]={{postload=function() end,directory="{world}",level="{world}.level",postlevel=function() end,displayName="{world}",description="Native SU accounting diagnostic"}}\n'
        worlds[world] = dict(cases=cases, mode=mode)
    put(campaign_path, campaign)
    original_files = index(Path(original["source"]))
    changed_keys = {name.lower() for name in altered}
    assert all(
        sha(source / n) == sha(path) for n, path in original_files.items() if n not in changed_keys
    )
    compiler = CACHE / "hwmp-testgrounds-step/lua4/lua-4.0.1/luac4-x86.exe"
    for relative in sorted(altered):
        path = source / relative
        result = subprocess.run([str(compiler), "-p", str(path)], capture_output=True)
        assert result.returncode == 0, (relative, result.stderr)
    probe = work / "query-check.lua"
    probe.write_text(query("check", "check"), encoding="ascii")
    result = subprocess.run([str(compiler), "-p", str(probe)], capture_output=True)
    assert result.returncode == 0, result.stderr
    verification = package_source(
        source, work / "release", "HWMPSUBoundaries.big", f"HWMP SU accounting scale{scale}"
    )
    record = dict(
        original,
        work=str(work),
        source=str(source),
        release=str(work / "release"),
        worlds=worlds,
        verification=verification,
        accounting_trial=True,
        experimental_scale=scale,
        runtime_token=token,
        changed_lua4_files=len(altered),
        normal_runtime_unchanged=True,
        baseline_work=original["work"],
    )
    save(work / "prepared.json", record)
    save(work / "previous-latest.json", dict(work=previous["work"]))
    save(boundary.WORK / "latest.json", dict(work=str(work)))
    print(
        json.dumps(dict(prepared=str(work), scale=scale, lua4_files=len(altered), archives=7)),
        flush=True,
    )


def collect(close):
    work = Path(json.loads((boundary.WORK / "current.json").read_text())["work"])
    proc = json.loads((work / "process.json").read_text())
    record = json.loads((Path(proc["prepared_work"]) / "prepared.json").read_text(encoding="utf8"))
    token = record["runtime_token"]
    log = GAME / "HomeworldRM/Bin/Release/HwRM.log"
    text, fresh = boundary.read_run_log(log, proc)
    markers = [
        line
        for line in text.splitlines()
        if fresh and "|token=" + token + "|" in line and "|world=" + proc["world"] + "|" in line
    ]
    # A matching freshly generated token is required before any terminal closure.
    errors = boundary.lua_errors(text) if fresh else []
    ended = any(
        "|event=end|" in line and "|world=" + proc["world"] + "|" in line for line in markers
    )
    status = "error" if errors else "finished" if ended else "running"
    if log.exists():
        shutil.copy2(log, work / "native-HwRM.log")
    report = dict(
        status=status,
        world=proc["world"],
        token=token,
        markers=markers,
        errors=errors,
        ui_test=False,
    )
    if close:
        assert fresh and (ended or errors), "Fresh owned endpoint/error not reached; game left open"
        pid = int(proc["pid"])
        script = f"$suOwned=Get-CimInstance Win32_Process -Filter 'ProcessId={pid}'; if ($suOwned -and $suOwned.Name -eq 'HomeworldRM.exe' -and $suOwned.CommandLine -like '*{boundary.CAMPAIGN}*' -and $suOwned.CommandLine -like '*{proc['world']}*') {{ Stop-Process -Id $suOwned.ProcessId }} else {{ throw 'Owned process identity changed' }}"
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", script], check=True, capture_output=True
        )
        report["owned_terminal_process_closed"] = True
    save(work / "accounting-result.json", report)
    print(
        json.dumps(
            dict(
                status=status,
                world=proc["world"],
                markers=len(markers),
                errors=errors,
                tail=markers[-9:],
            )
        ),
        flush=True,
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "install", "launch", "collect"])
    parser.add_argument("world", nargs="?", default="Hgn_Measure")
    parser.add_argument("--scale", type=int, choices=[32, 64], default=64)
    parser.add_argument("--close-terminal", action="store_true")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.scale)
    elif args.action == "install":
        print(boundary.install())
    elif args.action == "launch":
        boundary.launch(args.world, "Russian")
    else:
        collect(args.close_terminal)
