"""Isolated SU production boundaries. Never modifies normal release or Workshop."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import hashlib
import re

from hwrm_common import PROJECT, GAME, CACHE, index, save, sha
from hwrm_archive import package_source
from cataclysm import model
from auto_testgrounds import lua
from install_hwmp24 import active_processes, other_mod_files

WORK = PROJECT / "local/su-boundary-tests"
IDENTITY = "HWMP-SU-boundary-tests-v1"
CAMPAIGN = "HWMPSUBoundaries"
RACES = {"Hgn": "Hiigaran", "Vgr": "Vaygr", "Kus": "Kushan", "Tai": "Taiidan"}
KINDS = (
    "Control",
    "Under",
    "Exact",
    "Above",
    "Full",
    "Over",
    "Parallel",
    "ParallelExact",
    "Cancel",
    "Pause",
    "ProducerLoss",
    "FleetLoss",
)


def padding(total, ships):
    """Minimum number of single-hull filler entries, exact integer sum."""
    best = [None] * (total + 1)
    best[0] = []
    for value in range(1, total + 1):
        for ident, cost in ships:
            if cost <= value and best[value - cost] is not None:
                candidate = best[value - cost] + [ident]
                if best[value] is None or len(candidate) < len(best[value]):
                    best[value] = candidate
    if best[total] is None:
        raise ValueError(f"Cannot pad exact SU {total}")
    return best[total]


def worlds():
    design = model()
    result = {}
    for prefix, race in RACES.items():
        item = prefix.lower() + "_interceptor"
        cost = design["ships"][item]["su_per_group"]
        for kind in ("Auto", *KINDS):
            auto = kind == "Auto"
            definitions = (
                [
                    ("Control", 200, 1),
                    ("Under", cost - 1, 1),
                    ("Exact", cost, 1),
                    ("Above", cost + 1, 1),
                    ("Parallel", 2 * cost - 1, 2),
                    ("ParallelExact", 2 * cost, 2),
                ]
                if auto
                else [
                    (
                        kind,
                        {
                            "Control": 200,
                            "Under": cost - 1,
                            "Exact": cost,
                            "Above": cost + 1,
                            "Full": 0,
                            "Over": -1,
                            "Parallel": 2 * cost - 1,
                            "ParallelExact": 2 * cost,
                            "Cancel": 2 * cost - 1,
                            "Pause": 2 * cost - 1,
                            "ProducerLoss": 2 * cost - 1,
                            "FleetLoss": cost - 1,
                        }[kind],
                        (
                            2
                            if kind
                            in ("Parallel", "ParallelExact", "Cancel", "Pause", "ProducerLoss")
                            else 1
                        ),
                    )
                ]
            )
            cases = [
                dict(
                    id=name,
                    player=i + 1 if auto else 0,
                    free=free,
                    requests=requests,
                    builders=[
                        f"SUB_Carrier{i+1 if auto else 0}A",
                        f"SUB_Carrier{i+1 if auto else 0}B",
                    ],
                    mother=f"SUB_Mother{i+1 if auto else 0}",
                    volume=f"SUB_Volume{i+1 if auto else 0}",
                )
                for i, (name, free, requests) in enumerate(definitions)
            ]
            for case in cases:
                case["extra"] = (
                    design["ships"][prefix.lower() + "_resourcecollector"]["su_per_group"]
                    if case["id"] == "FleetLoss"
                    else 0
                )
            fillers = [
                (ident, row["su_per_group"])
                for ident, row in design["ships"].items()
                if ident.startswith(prefix.lower() + "_")
                and row["build_batch"] == 1
                and not any(
                    word in ident
                    for word in (
                        "carrier",
                        "mothership",
                        "shipyard",
                        "research",
                        "probe",
                        "sensor",
                        "interceptor",
                    )
                )
                and row["su_per_group"] > 0
            ]
            plans = {
                profile: {
                    c["id"]: padding(budget - c["free"] - 80 - c["extra"], fillers) for c in cases
                }
                for profile, budget in design["budgets"].items()
            }
            for profile, entries in plans.items():
                for c in cases:
                    assert (
                        sum(design["ships"][ship]["su_per_group"] for ship in entries[c["id"]])
                        + 80
                        + c["extra"]
                        == design["budgets"][profile] - c["free"]
                    )
            result[prefix + "_" + kind] = dict(
                race=race,
                prefix=prefix.lower(),
                auto=auto,
                item=item,
                cost=cost,
                cases=cases,
                padding=plans,
            )
    return result


def prepare():
    manifest = json.loads(
        (PROJECT / "local/hwmp-patch-2.4/manifest.json").read_text(encoding="utf8")
    )
    base = Path(manifest["source"])
    assert {n: sha(p) for n, p in index(base).items()} == manifest["files"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    work = WORK / stamp
    source = work / "source"
    release = work / "release"
    work.mkdir(parents=True)
    shutil.copytree(base, source)

    def put(name, text):
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="ascii", newline="\n")

    spec = worlds()
    campaign = [
        'displayName="$9988000"',
        f'contentName="{CAMPAIGN}"',
        "contentType=2",
        "contentOrdered=0",
        'contentChooseText="$3492"',
        'contentThumbName="$9988000"',
        'contentThumbDesc="$9988001"',
        'contentRules="hwmpcataclysm"',
        'ExtFilter="campaign_gbx"',
        "Mission={}",
    ]
    strings = {
        9988000: ("HWMP: граничные тесты SU", "HWMP: SU boundary tests"),
        9988001: (
            "Стройте ПЕРЕХВАТЧИКИ. Два авианосца рядом; наполнитель вдали. Счётчик — только готовый флот. Действия и ожидания — в инструкции SU_BOUNDARY_TESTS.md.",
            "Build INTERCEPTORS. Two carriers nearby; filler fleet far away. HUD counts owned units only. See SU_BOUNDARY_TESTS.md for actions and expectations.",
        ),
    }
    for number, (name, w) in enumerate(spec.items(), 1):
        key = 9988010 + number
        strings[key] = (name, name)
        folder = f"leveldata/campaign/{CAMPAIGN}/{name}"
        lines = ["function DetermChunk()"]
        players = len(w["cases"]) + 1 if w["auto"] else 2
        for player in range(players):
            x = player * 40000 - 100000

            def ship(group, ident, pos):
                lines.extend(
                    [
                        f"addSquadron({lua(group)},{lua(ident)},{lua(pos)},{player},{{0,0,0}},1,0)",
                        f"createSOBGroup({lua(group)})",
                        f"addToSOBGroup({lua(group)},{lua(group)})",
                    ]
                )

            ship(f"SUB_Mother{player}", w["prefix"] + "_mothership", [x, 0, 9000])
            if any(c["player"] == player for c in w["cases"]):
                ship(f"SUB_Carrier{player}A", w["prefix"] + "_carrier", [x, 0, 0])
                ship(f"SUB_Carrier{player}B", w["prefix"] + "_carrier", [x + 2500, 0, 0])
                lines.append(f'addSphere("SUB_Volume{player}",{{{x},0,40000}},15000)')
                if name.endswith("_FleetLoss"):
                    ship("SUB_Release", w["prefix"] + "_resourcecollector", [x, 0, 3500])
        lines += [
            'addCamera("SUB_Home",{-98750,0,0},{-93500,5500,-7000})',
            "setWorldBoundsInner({0,0,0},{300000,100000,300000})",
            "end",
            "function NonDetermChunk()",
            'loadBackground("m01")',
            "setSensorsManagerCameraDistances(100,1000000)",
            "end",
            f"maxPlayers={players}",
            f'levelDesc="${key}"',
            "player={}",
        ]
        for player in range(players):
            lines.append(
                f'player[{player}]={{id={player},name="",resources=100000,raceName="{w["race"]}",startPos=0}}'
            )
        put(folder + f"/{name}.level", "\n".join(lines))
        put(
            folder + f"/{name}.lua",
            f'SUB_HW1={int(w["prefix"] in ("kus", "tai"))}\nSUB_World={lua(name)}\nSUB_Auto={int(w["auto"])}\nSUB_Item={lua(w["item"])}\nSUB_ItemID={lua(w["item"].upper())}\nSUB_Cost={w["cost"]}\nSUB_Cases={lua(w["cases"])}\nSUB_Padding={lua(w["padding"])}\ndofilepath("data:scripts/hwmp24/su_boundary.lua")\ndofilepath("data:scripts/rules/hwmpcataclysm.lua")',
        )
        campaign.append(
            f'Mission[{number}]={{postload=function() end,directory="{name}",level="{name}.level",postlevel=function() end,displayName="${key}",description="$9988001"}}'
        )
    put(f"leveldata/campaign/{CAMPAIGN}.campaign", "\n".join(campaign))
    shutil.copy2(PROJECT / "autotests/su_boundary.lua", source / "scripts/hwmp24/su_boundary.lua")
    path = source / "scripts/rules/hwmpcataclysm.lua"
    text = path.read_text()
    assert text.count("SinglePlayer = 0") == 1
    put(str(path.relative_to(source)), text.replace("SinglePlayer = 0", "SinglePlayer = 1"))
    path = source / "scripts/rules/deathmatch/deathmatch.lua"
    text = path.read_text()
    needle = '\t\tRule_AddInterval("timer_updating",1.02)'
    assert text.count(needle) == 1
    put(
        str(path.relative_to(source)),
        text.replace(needle, '    Rule_AddInterval("SUB_Init",4)\n' + needle),
    )
    path = source / "locale/localedat.lua"
    text = path.read_text()
    end = text.rfind("}")
    put(str(path.relative_to(source)), text[:end] + '    {name="hwmp_su_tests.dat"},\n}')
    for language in ("English", "Russian", "French", "German", "Italian", "Spanish"):
        records = "".join(
            str(k) + "\t" + v[0 if language == "Russian" else 1] + "\r\n"
            for k, v in sorted(strings.items())
        )
        (source / f"locale/{language}/hwmp_su_tests.ucs").write_bytes(records.encode("utf-16"))
    altered = {
        "scripts/rules/hwmpcataclysm.lua",
        "scripts/rules/deathmatch/deathmatch.lua",
        "locale/localedat.lua",
    }
    # Print actual definition-mode selection, without changing its fields/calls.
    for prefix in ("hgn", "vgr", "kus", "tai"):
        for kind in ("interceptor", "carrier", "resourcecontroller"):
            ident = prefix + "_" + kind
            relative = f"ship/{ident}/{ident}.ship"
            path = source / relative
            if not path.exists():
                continue
            text = path.read_text(encoding="ascii")
            text += (
                '\nprint("HWMP_SUB_SHIP|id=' + ident + '|cat=" .. tostring(HWMP_CataclysmShip))\n'
            )
            put(relative, text)
            altered.add(relative)
    assert all(sha(source / n) == h for n, h in manifest["files"].items() if n not in altered)
    compiler = CACHE / "hwmp-testgrounds-step/lua4/lua-4.0.1/luac4-x86.exe"
    parsed = 0
    for n, path in index(source).items():
        if (n not in manifest["files"] or n in altered) and path.suffix in (
            ".lua",
            ".level",
            ".campaign",
        ):
            proc = subprocess.run([str(compiler), "-p", str(path)], capture_output=True, text=True)
            assert proc.returncode == 0, (n, proc.stderr)
            parsed += 1
    verified = package_source(source, release, "HWMPSUBoundaries.big", "HWMP SU Boundary Tests")
    result = dict(
        identity=IDENTITY,
        work=str(work),
        source=str(source),
        release=str(release),
        source_fix=manifest["fix_revision"],
        worlds=spec,
        verification=verified,
        lua4_parsed=parsed,
        normal_runtime_preserved=True,
    )
    save(work / "prepared.json", result)
    save(WORK / "latest.json", dict(work=str(work)))
    print(
        json.dumps(dict(prepared=True, worlds=len(spec), lua4_parsed=parsed, work=str(work))),
        flush=True,
    )


def prepared():
    return json.loads(
        (Path(json.loads((WORK / "latest.json").read_text())["work"]) / "prepared.json").read_text(
            encoding="utf8"
        )
    )


def install():
    record = prepared()
    assert not active_processes(GAME), "Close game/launcher; no process was stopped"
    mods = (GAME / "HomeworldRM/DataWorkshopMODs").resolve(strict=True)
    target = (mods / CAMPAIGN).resolve()
    assert target.parent == mods and not target.is_symlink() and not target.is_junction()
    if target.exists():
        assert (target / "owner.txt").read_text().strip() == IDENTITY
        backup = Path(record["work"]) / (
            "previous-install-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        )
        shutil.copytree(target, backup)
    before = other_mod_files(mods, target)
    target.mkdir(exist_ok=True)
    for row in record["verification"]["archives"]:
        path = Path(row["archive"])
        assert sha(path) == row["sha256"]
        shutil.copy2(path, target / path.name)
        assert sha(target / path.name) == row["sha256"]
    (target / "owner.txt").write_text(IDENTITY + "\n")
    assert before == other_mod_files(mods, target)
    save(
        WORK / "installed.json",
        dict(work=record["work"], target=str(target), other_mods_preserved=True),
    )
    return target


def launch(world, language):
    r = prepared()
    assert world in r["worlds"]
    assert not active_processes(GAME), "Game/launcher already running; nothing was stopped"
    installed = json.loads((WORK / "installed.json").read_text())
    assert installed["work"] == r["work"]
    for row in r["verification"]["archives"]:
        assert sha(Path(installed["target"]) / Path(row["archive"]).name) == row["sha256"]
    work = Path(r["work"]) / "runs" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    work.mkdir(parents=True)
    log = GAME / "HomeworldRM/Bin/Release/HwRM.log"
    if log.exists():
        shutil.copy2(log, work / "preceding-HwRM.log")
    exe = GAME / "HomeworldRM/Bin/Release/HomeworldRM.exe"
    cmd = [
        str(exe),
        "-workshopmod",
        CAMPAIGN + "\\HWMPSUBoundaries.big",
        "-campaign",
        CAMPAIGN,
        "-startinglevel",
        world,
        "-windowed",
        "-w",
        "1600",
        "-h",
        "900",
        "-locale",
        language,
        "-nomovies",
        "-luatrace",
    ]
    previous_log_sha256 = sha(log) if log.exists() else None
    started_ns = time.time_ns()
    proc = subprocess.Popen(
        cmd,
        cwd=exe.parent,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    save(
        work / "process.json",
        dict(
            pid=proc.pid,
            world=world,
            command=cmd,
            prepared_work=r["work"],
            started_ns=started_ns,
            previous_log_sha256=previous_log_sha256,
        ),
    )
    save(WORK / "current.json", dict(work=str(work)))
    print(json.dumps(dict(launched=True, pid=proc.pid, world=world, log=str(work))), flush=True)


def read_run_log(log, process):
    """A repeated world/package token cannot make a preceding run's log fresh."""
    try:
        modified_ns = log.stat().st_mtime_ns
        raw = log.read_bytes()
    except FileNotFoundError:
        return "", False
    text = raw.decode(
        "utf-16" if raw.startswith(b"\xff\xfe") else "utf8", errors="replace"
    ).replace("\0", "")
    fresh = (
        bool(raw)
        and "started_ns" in process
        and modified_ns >= process["started_ns"]
        and hashlib.sha256(raw).hexdigest() != process.get("previous_log_sha256")
    )
    return text, fresh


def lua_errors(text):
    return [
        line
        for line in text.splitlines()
        if re.search(
            r"attempt to|stack traceback|FATAL|Assertion failed|syntax error|expected near|unexpected symbol|invalid number of arguments",
            line,
            re.I,
        )
    ]


def collect(close):
    work = Path(json.loads((WORK / "current.json").read_text())["work"])
    process = json.loads((work / "process.json").read_text())
    log = GAME / "HomeworldRM/Bin/Release/HwRM.log"
    text, fresh = read_run_log(log, process)
    if log.exists():
        shutil.copy2(log, work / "native-HwRM.log")
    markers = [
        line
        for line in text.splitlines()
        if fresh and "HWMP_SUB|" in line and "|world=" + process["world"] + "|" in line
    ]
    errors = lua_errors(text) if fresh else []
    ended = any("event=end|" in line for line in markers)
    results = [line for line in markers if "event=result|" in line]
    status = "error" if errors else "finished" if ended else "running_or_manual"
    if ended and (len(results) != 6 or any("status=passed|" not in line for line in results)):
        status = "needs_review"
    report = dict(
        status=status, world=process["world"], markers=markers, errors=errors, ui_test=False
    )
    if close:
        assert fresh and (ended or errors), "Fresh owned endpoint/error required; game is left open"
        pid = int(process["pid"])
        script = f"$suTest=Get-CimInstance Win32_Process -Filter 'ProcessId={pid}'; if ($suTest -and $suTest.Name -eq 'HomeworldRM.exe' -and $suTest.CommandLine -like '*{CAMPAIGN}*' -and $suTest.CommandLine -like '*{process['world']}*') {{ Stop-Process -Id $suTest.ProcessId }} else {{ throw 'Owned process identity changed' }}"
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", script], check=True, capture_output=True
        )
        report["owned_terminal_process_closed"] = True
    save(work / "result.json", report)
    print(
        json.dumps(
            dict(
                status=report["status"],
                world=report["world"],
                errors=errors,
                results=results,
                markers_tail=markers[-8:],
            )
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "install", "launch", "collect"])
    parser.add_argument("world", nargs="?", default="Hgn_Exact")
    parser.add_argument("--language", default="Russian", choices=["Russian", "English"])
    parser.add_argument("--close-terminal", action="store_true")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.action == "install":
        print(install())
    elif args.action == "launch":
        launch(args.world, args.language)
    else:
        collect(args.close_terminal)
