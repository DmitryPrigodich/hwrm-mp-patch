"""Install the verified diagnostic release in its own folder; never launch."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil

from hwrm_common import GAME, PROJECT, index, save, sha
from install_hwmp24 import active_processes, other_mod_files
from testgrounds import IDENTITY, RELEASE, WORK

PAYLOAD = {
    "HWMPTestGrounds.big",
    "English.big",
    "Russian.big",
    "config.txt",
    "TEST_GROUNDS.md",
    "version.json",
    "HWMP Test Grounds.cmd",
    "start_testgrounds.ps1",
}
MARKER = "package-id.txt"


def install(game_root=GAME, apply=False):
    game = Path(game_root).resolve(strict=True)
    mods = (game / "HomeworldRM/DataWorkshopMODs").resolve(strict=True)
    target = (mods / "HWMPTestGrounds").resolve()
    if (
        target.parent != mods
        or target.name != "HWMPTestGrounds"
        or target.is_symlink()
        or target.is_junction()
    ):
        raise ValueError("Unsafe diagnostic installation target")
    sums = {}
    for line in (RELEASE / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines():
        m = re.fullmatch(r"([0-9a-f]{64})  ([^/\\]+)", line)
        if not m or m[2] in sums:
            raise ValueError("Invalid release checksums")
        sums[m[2]] = m[1]
    if set(sums) != PAYLOAD or {p.name for p in RELEASE.iterdir()} != PAYLOAD | {"SHA256SUMS.txt"}:
        raise ValueError("Unexpected diagnostic release files")
    for name, digest in sums.items():
        if sha(RELEASE / name) != digest:
            raise ValueError("Release checksum mismatch: " + name)
    version = json.loads((RELEASE / "version.json").read_text(encoding="utf8"))
    checked = json.loads((WORK / "verification-package.json").read_text(encoding="utf8"))
    source_check = json.loads((WORK / "verification-source.json").read_text(encoding="utf8"))
    if (
        version["identity"] != IDENTITY
        or source_check["revision"] != version["revision"]
        or source_check["status"] != "passed"
    ):
        raise ValueError("Source verification does not match the release")
    if checked["status"] != "passed" or not checked["full_extract_hash_comparison"]:
        raise ValueError("Full archive payload verification is required")
    verified = {Path(a["archive"]).name: a["sha256"] for a in checked["archives"]}
    for name in ("HWMPTestGrounds.big", "English.big", "Russian.big"):
        if verified.get(name) != sums[name]:
            raise ValueError("Stale archive verification: " + name)
    sums["SHA256SUMS.txt"] = sha(RELEASE / "SHA256SUMS.txt")
    if target.exists():
        if not (target / MARKER).is_file() or (target / MARKER).read_text().strip() != IDENTITY:
            raise ValueError("Existing target is not an owned diagnostic installation")
        if set(index(target)) - {n.lower() for n in set(sums) | {MARKER}}:
            raise ValueError("Existing diagnostic target contains unowned files")
        if any(p.is_symlink() or p.is_junction() for p in target.rglob("*")):
            raise ValueError("Links are not allowed inside the diagnostic target")
    result = {
        "identity": IDENTITY,
        "revision": version["revision"],
        "target": str(target),
        "files": sums,
        "installed": False,
        "launched": False,
        "engine_tested": False,
    }
    if not apply:
        return result
    running = active_processes(game)
    if running:
        raise RuntimeError(
            "Close the running game/launcher yourself before installation: " + repr(running)
        )
    before = other_mod_files(mods, target)
    protected = [game / "HomeworldRM/Data/BananaDLC.big"]
    for folder in ("HWMPPatch24", "VastReachesMiniCampaign", "Gearbox/BananaMothership"):
        protected.extend((mods / folder).glob("*.big"))
    guard = {str(p): sha(p) for p in protected if p.is_file()}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    if target.exists():
        backup = PROJECT / "local/installed-backups" / stamp / "HWMPTestGrounds"
        shutil.copytree(target, backup)
        assert {n: sha(p) for n, p in index(target).items()} == {
            n: sha(p) for n, p in index(backup).items()
        }
        result["backup"] = str(backup)
    target.mkdir(exist_ok=True)
    for name, digest in sums.items():
        temporary = target / (".hwmt-" + name)
        if temporary.exists():
            raise ValueError("Unexpected staging file: " + str(temporary))
        shutil.copy2(RELEASE / name, temporary)
        assert sha(temporary) == digest
        temporary.replace(target / name)
    (target / MARKER).write_text(IDENTITY + "\n", encoding="ascii")
    assert {n: sha(target / n) for n in sums} == sums
    assert other_mod_files(mods, target) == before, "Other mod files changed"
    assert {n: sha(Path(n)) for n in guard} == guard, "Protected game archives changed"
    result.update(
        installed=True, installed_at_utc=stamp, other_mods_unchanged=True, protected_hashes=guard
    )
    save(WORK / "installation.json", result)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--install", action="store_true")
    p.add_argument("--game-root", type=Path, default=GAME)
    args = p.parse_args()
    print(json.dumps(install(args.game_root, args.install), ensure_ascii=False, indent=2))
