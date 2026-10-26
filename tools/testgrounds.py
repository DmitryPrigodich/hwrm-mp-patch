"""Build a separate Extra Missions diagnostic package. Never install or launch.

Compose the already prepared full HWMP source plus isolated SCAR/menu resources.
No gameplay definition may change, and neither consumers nor normal release move.
"""

import argparse
from project_credits import SHORT_CREDITS
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil

from hwrm_common import PROJECT, CACHE, build_directory, index, save, sha

ROOT = PROJECT / "testgrounds"
WORK = PROJECT / "local/testgrounds"
RELEASE = PROJECT / "local/HWMPTestGrounds-release"
BUILD = build_directory("hwmp-testgrounds", PROJECT)
SOURCE = BUILD / "source"
COLLECTION = "HWMP24TestGrounds"
MISSIONS = [
    ("GravityOverlap", "gravity", 9984010, 9984012),
    ("InterceptorWithdrawal", "assault", 9984020, 9984022),
    ("MissileTargetLoss", "missiles", 9984030, 9984032),
]
IDENTITY = "HWMP-TestGrounds-v1"
THUMB = (
    CACHE
    / "players-patch-audit/rm-campaign-hw2/ui/mapthumbnails/campaign/ascension/m03_staging.dds"
)
REGISTRY = CACHE / "players-patch-audit/rm-base/locale/localedat.lua"


def digest_tree(folder):
    return {n: sha(p) for n, p in index(folder).items()}


def put(name, text, encoding="ascii", newline="\n"):
    p = SOURCE / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text + "\n", encoding=encoding, newline=newline)


def level(chapter, script, title):
    ships = [
        (
            "HWT_Anchor",
            "kus_mothership" if script == "gravity" else "vgr_mothership",
            (0, 0, -24000),
            0,
            1,
        )
    ]
    volumes = []
    if script == "gravity":
        for prefix, race, x in [("Kus", "kus", -8000), ("Tai", "tai", 8000)]:
            ships += [
                (f"HWT_{prefix}A", f"{race}_gravwellgenerator", (x - 500, 0, 0), 0, 1),
                (f"HWT_{prefix}B", f"{race}_gravwellgenerator", (x + 500, 0, 0), 0, 1),
                (f"HWT_{prefix}Friendly", "hgn_interceptor", (x, 0, 1000), 0, 0),
                (f"HWT_{prefix}Enemy", "hgn_assaultcorvette", (x, 0, 1800), 1, 0),
            ]
        camera = ((0, 0, 0), (0, 15000, -16000))
    elif script == "assault":
        for i, x in enumerate([-15000, -5000, 5000, 15000], 1):
            ships += [
                (f"HWT_Assault{i}", "vgr_assaultfrigate", (x, 0, 0), 0, 1),
                (f"HWT_Target{i}", "hgn_interceptor", (x, 0, 1300), 1 if i < 3 else 2, 0),
            ]
            volumes.append((f"HWT_Retreat{i}", (x, 0, 18000), 100))
        camera = ((0, 0, 1500), (0, 22000, -17000))
    else:
        ships += [
            ("HWT_Launcher", "vgr_heavymissilefrigate", (0, 0, 0), 0, 1),
            ("HWT_Primary", "hgn_torpedofrigate", (0, 0, 2200), 1, 1),
            ("HWT_Replacement", "hgn_torpedofrigate", (600, 0, 2400), 1, 1),
        ]
        camera = ((0, 0, 1200), (4000, 4500, -4500))

    def vec(v):
        return "{" + ",".join(str(x) for x in v) + "}"

    lines = ["function DetermChunk()"]
    for name, kind, pos, owner, size in ships:
        lines += [
            f'addSquadron("{name}","{kind}",{vec(pos)},{owner},{{0,0,0}},{size},0)',
            f'createSOBGroup("{name}")',
            f'addToSOBGroup("{name}","{name}")',
        ]
    for name, pos, radius in volumes:
        lines.append(f'addSphere("{name}",{vec(pos)},{radius})')
    lines += [
        f'addCamera("HWT_Home",{vec(camera[0])},{vec(camera[1])})',
        "setWorldBoundsInner({0,0,0},{42000,30000,42000})",
        "end",
        "function NonDetermChunk()",
        'loadBackground("m01")',
        "setSensorsManagerCameraDistances(100,100000)",
        "end",
        f'levelDesc="${title}"',
        f'maxPlayers={3 if script == "assault" else 2}',
        "player={}",
        f'player[0]={{id=0,name="",resources=0,raceName="{"Kushan" if script == "gravity" else "Vaygr"}",startPos=0}}',
        'player[1]={id=1,name="",resources=0,raceName="Hiigaran",startPos=0}',
    ]
    if script == "assault":
        lines.append('player[2]={id=2,name="",resources=0,raceName="Hiigaran",startPos=0}')
    return "\n".join(lines), ships


def read_ucs(path):
    raw = path.read_bytes()
    return (
        raw.decode("utf-16")
        if raw.startswith((b"\xff\xfe", b"\xfe\xff"))
        else raw.decode("utf-8-sig", errors="replace")
    )


def prepare():
    base_manifest = json.loads(
        (PROJECT / "local/hwmp-patch-2.4/manifest.json").read_text(encoding="utf8")
    )
    base = Path(base_manifest["source"]).resolve(strict=True)
    baseline = digest_tree(base)
    if not baseline or not (base / "scripts/hwmp24/effects.lua").is_file():
        raise ValueError("Prepare the normal HWMP source first.")
    strings = json.loads((ROOT / "strings.json").read_text(encoding="utf8"))
    for n, p in index(base).items():
        if n.endswith(".ucs"):
            used = set(re.findall(r"^\s*(\d+)\s", read_ucs(p), re.M))
            if used & set(strings):
                raise ValueError("UCS collision: " + n)
    owned = BUILD / "owner.txt"
    if SOURCE.exists():
        if (
            SOURCE.resolve().parent != BUILD.resolve()
            or not owned.is_file()
            or owned.read_text() != IDENTITY
        ):
            raise ValueError("Refusing unowned build directory.")
        shutil.rmtree(SOURCE)
    owned.write_text(IDENTITY, encoding="ascii")
    shutil.copytree(base, SOURCE)
    overlays = digest_tree(ROOT / "overrides")
    for name, p in index(ROOT / "overrides").items():
        if name in baseline:
            raise ValueError("Diagnostic overlay replaces existing runtime: " + name)
        dest = SOURCE / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
    registry_text = REGISTRY.read_text(encoding="ascii")
    if "hwmp_testgrounds.dat" in registry_text:
        raise ValueError("Unexpected pre-existing test dictionary")
    registry_end = registry_text.rfind("}")
    if registry_end < 0:
        raise ValueError("Invalid native dictionary registry")
    put(
        "locale/localedat.lua",
        registry_text[:registry_end] + '    {name="hwmp_testgrounds.dat"},\n}\n',
    )
    revision = hashlib.sha256(
        json.dumps(
            {
                "scripts": overlays,
                "strings": strings,
                "builder": sha(Path(__file__)),
                "registry": sha(REGISTRY),
                "base": baseline,
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    put("scripts/hwmp24/testgrounds/version.lua", f'HWT_REVISION="{revision}"')
    lines = [
        'displayName="$9984000"',
        "contentType=2",
        f'contentName="{COLLECTION}"',
        "contentOrdered=0",
        'contentChooseText="$3492"',
        'contentThumbName="$9984000"',
        'contentThumbDesc="$9984000"',
        "contentSort=0.25",
        'contentRules="SinglePlayer"',
        'ExtFilter="campaign_gbx"',
        "Mission={}",
    ]
    fixtures = {}
    if not THUMB.is_file():
        raise FileNotFoundError("Extract the native campaign thumbnail: " + str(THUMB))
    # Native Extra Missions uses a sibling .dds next to the .campaign file.
    # Chapter thumbnails under UI/MapThumbnails are a separate resource.
    cover = SOURCE / f"leveldata/campaign/{COLLECTION}.dds"
    cover.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(THUMB, cover)
    for i, (chapter, script, title, desc) in enumerate(MISSIONS, 1):
        lines.append(
            f'Mission[{i}]={{postload=function() end,directory="{chapter}",level="{chapter}.level",postlevel=function() end,displayName="${title}",description="${desc}"}}'
        )
        text, fixtures[chapter] = level(chapter, script, title)
        put(f"leveldata/campaign/{COLLECTION}/{chapter}/{chapter}.level", text)
        put(
            f"leveldata/campaign/{COLLECTION}/{chapter}/{chapter}.lua",
            f'dofilepath("data:scripts/hwmp24/testgrounds/{script}.lua")',
        )
        p = SOURCE / f"ui/mapthumbnails/campaign/{COLLECTION}/{chapter}.dds"
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(THUMB, p)
    put(f"leveldata/campaign/{COLLECTION}.campaign", "\n".join(lines))
    for i, lang in enumerate(("Russian", "English")):
        entries = []
        for number, pair in sorted(strings.items()):
            if len(pair) != 2 or not all(pair) or pair[0] == pair[1]:
                raise ValueError("Invalid RU/EN pair")
            entries.append(number + "\t" + pair[i])
        put(f"locale/{lang}/hwmp_testgrounds.ucs", "\n".join(entries), "utf-16", newline="\r\n")
    actual = digest_tree(SOURCE)
    changed = [n for n in baseline if actual.get(n) != baseline[n]]
    if changed:
        raise ValueError("Base runtime changed: " + repr(changed))
    additions = {n: h for n, h in actual.items() if n not in baseline}
    allowed = (
        "scripts/hwmp24/testgrounds/",
        "leveldata/campaign/" + COLLECTION.lower(),
        "ui/mapthumbnails/campaign/" + COLLECTION.lower() + "/",
        "locale/",
    )
    if any(not n.startswith(allowed) for n in additions):
        raise ValueError("Unexpected test resource")
    result = {
        "identity": IDENTITY,
        "revision": revision,
        "source": str(SOURCE),
        "base_source": str(base),
        "base_files": baseline,
        "base_runtime_unchanged": True,
        "additions": additions,
        "fixtures": fixtures,
        "strings": len(strings),
        "thumbnail_source": str(THUMB),
        "thumbnail_sha256": sha(THUMB),
        "dictionary_registry_source": str(REGISTRY),
        "dictionary_registry_sha256": sha(REGISTRY),
        "engine_tested": False,
        "installed": False,
        "launched": False,
    }
    save(WORK / "source.json", result)
    return result


def package():
    from hwrm_archive import package_source

    result = prepare()
    verification = package_source(SOURCE, RELEASE, "HWMPTestGrounds.big", "HWMP Test Grounds")
    for p in RELEASE.glob("*.log"):
        shutil.move(str(p), str(WORK / p.name))
    for name in ("start_testgrounds.ps1", "HWMP Test Grounds.cmd"):
        shutil.copy2(ROOT / name, RELEASE / name)
    shutil.copy2(PROJECT / "docs/TEST_GROUNDS.md", RELEASE / "TEST_GROUNDS.md")
    (RELEASE / "config.txt").write_text(
        "Title: HWMP 2.4 Test Grounds\n\nTags: Test\nGameType: HomeworldRM\nModType: MOD\nBigFilename: HWMPTestGrounds.big\n\nDescription:\nStandalone diagnostic Extra Missions; not the normal balance release.\n"
        + SHORT_CREDITS
        + "\n",
        encoding="ascii",
    )
    save(
        RELEASE / "version.json",
        {
            k: result[k]
            for k in (
                "identity",
                "revision",
                "base_runtime_unchanged",
                "engine_tested",
                "installed",
                "launched",
            )
        },
    )
    files = {
        p.name: sha(p) for p in RELEASE.iterdir() if p.is_file() and p.name != "SHA256SUMS.txt"
    }
    (RELEASE / "SHA256SUMS.txt").write_text(
        "".join(h + "  " + n + "\n" for n, h in sorted(files.items())), encoding="ascii"
    )
    save(WORK / "verification-package.json", verification)
    save(
        WORK / "release.json",
        {
            "release": str(RELEASE),
            "revision": result["revision"],
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "files": files,
            "native_status": "not_run",
            "installed": False,
            "launched": False,
        },
    )
    return {
        "release": str(RELEASE),
        "files": len(files) + 1,
        "revision": result["revision"],
        "full_payload_verification": verification["status"],
        "engine_tested": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    result = package() if args.package else prepare()
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("base_files", "additions", "fixtures")},
            ensure_ascii=False,
            indent=2,
        )
    )
