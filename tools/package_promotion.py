"""Promote a freshly checked package, preserving prior contents and rolling back on failure."""

from tool_safety import require
import json
from pathlib import Path


def promote(stage, target, work, owned_root, identity, stamp):
    stage, target, work, owned_root = map(Path, (stage, target, work, owned_root))
    require(target.parent.resolve() == owned_root.resolve(), "Release target outside owned root")
    require(stage.resolve().is_relative_to(work.resolve()), "Stage outside build work directory")
    require(not target.is_symlink() and not target.is_junction(), "Linked release target")
    require(not stage.is_symlink() and not stage.is_junction(), "Linked staging directory")
    require(
        not any(p.is_symlink() or p.is_junction() for p in stage.rglob("*")),
        "Links in staged package",
    )
    backup = None
    if target.exists():
        marker = target / "version.json"
        require(
            marker.is_file()
            and json.loads(marker.read_text(encoding="utf8")).get("identity") == identity,
            "Refuse unowned release directory",
        )
        backup = work / ("previous-package-" + stamp)
        require(not backup.exists(), "Occupied backup path")
        target.replace(backup)
    try:
        stage.replace(target)
    except Exception:
        if backup is not None and not target.exists():
            backup.replace(target)
        raise
    return backup
