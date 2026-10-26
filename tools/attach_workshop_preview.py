"""Attach an owner-selected cover to existing, unpublished Workshop staging only."""

import argparse
import json
from pathlib import Path
import re
import shutil

from hwrm_common import PROJECT, save, sha


def attach(source):
    from PIL import Image

    latest = json.loads((PROJECT / "local/workshop-latest.json").read_text(encoding="utf8"))
    root = Path(latest["root"]).resolve(strict=True)
    allowed = (PROJECT / "local/Workshop-upload").resolve(strict=True)
    if not root.is_relative_to(allowed) or root == allowed or root.is_symlink():
        raise ValueError("Unsafe staging root.")
    content = root / "content"
    metadata_path = root / "preparation.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf8"))
    if metadata.get("identity") != "HWMP-workshop-preparation-v1" or metadata.get("published"):
        raise ValueError("Not an owned unpublished draft.")
    config = (content / "config.txt").read_text(encoding="utf8")
    if not re.search(r"(?m)^WorkshopID:\s*0\s*$", config):
        raise ValueError("An existing Workshop item requires the update workflow.")
    source = Path(source).resolve(strict=True)
    target = content / "preview.jpg"
    if target.exists():
        if metadata.get("preview_sha256") != sha(target):
            raise ValueError("Existing preview changed outside this draft.")
        shutil.copy2(target, root / "previous-owned-preview.jpg")
    with Image.open(source) as image:
        if image.width != image.height:
            raise ValueError("Supply the approved square composition; no automatic crop.")
        # Export rendition only: preserve the composition, wording and artwork.
        image.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS).save(
            target, format="JPEG", quality=94, optimize=True
        )
    if target.stat().st_size >= 1024 * 1024:
        raise ValueError("Toolkit preview exceeds1MiB.")
    metadata.update(
        preview_sha256=sha(target),
        artwork_kind="owner_selected_illustrative_cover",
        preview_source_sha256=sha(source),
        ready_for_owner_review=True,
        published=False,
    )
    save(metadata_path, metadata)
    return {
        "preview": str(target),
        "size": [512, 512],
        "bytes": target.stat().st_size,
        "sha256": sha(target),
        "published": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    print(json.dumps(attach(args.source), indent=2))
