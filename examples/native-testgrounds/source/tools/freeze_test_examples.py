"""Create or verify a frozen text-only test-source archive, outside runtime composition."""

import argparse
import json
from pathlib import Path
import shutil

from hwrm_common import PROJECT, index, save, sha

DESTINATION = PROJECT / "examples/native-testgrounds/source"
MANIFEST = DESTINATION.parent / "snapshot.json"


def create():
    if DESTINATION.exists() or MANIFEST.exists():
        raise ValueError("Frozen archive already exists; never silently refresh reviewed examples.")
    paths = []
    for folder in (
        PROJECT / "autotests",
        PROJECT / "testgrounds",
        PROJECT / "tools/templates",
        PROJECT / "hwmp-patch-2.4/overrides/scripts/hwmp24",
    ):
        paths.extend(
            path
            for path in folder.rglob("*")
            if path.is_file()
            and path.suffix.lower() in (".lua", ".level", ".campaign", ".py", ".md")
        )
    paths.extend((PROJECT / "tools").glob("*.py"))
    records = {}
    for path in sorted(set(paths)):
        name = path.relative_to(PROJECT).as_posix()
        target = DESTINATION / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        if sha(target) != sha(path):
            raise RuntimeError("Snapshot copy differs: " + name)
        records[name] = sha(path)
    save(
        MANIFEST,
        {
            "identity": "HWMP-native-examples-2026-10-26",
            "purpose": "frozen_source_reference_not_runtime",
            "files": records,
            "assets_logs_saves_included": False,
        },
    )
    return verify()


def verify():
    expected = json.loads(MANIFEST.read_text(encoding="utf8"))["files"]
    actual = {
        path.relative_to(DESTINATION).as_posix(): sha(path)
        for path in DESTINATION.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        raise ValueError(
            "Frozen snapshot changed; preserve provenance instead of silently replacing it."
        )
    return {"status": "passed", "text_files": len(expected), "runtime_imported": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args()
    print(json.dumps(create() if args.create else verify()))
