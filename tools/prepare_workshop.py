"""Stage the official Toolkit's loose-file input. Never calls Steam/create/update."""

import argparse
import json
from pathlib import Path
import shutil

from hwrm_common import PROJECT, index, save, sha
from hwmp24 import SOURCE, WORK
from install_hwmp24 import release_files


def workshop_item_id():
    """Retain the first publication identity across subsequent source revisions."""
    path = PROJECT / "workshop/item.json"
    if not path.exists():
        return "0"
    item = json.loads(path.read_text(encoding="utf8"))
    identifier = str(item["workshop_id"])
    if not identifier.isdecimal() or int(identifier) < 1 or item["consumer_app_id"] != 244160:
        raise ValueError("Invalid pinned Homeworld Workshop identity.")
    return identifier


def prepare(preview=None):
    from PIL import Image

    release_files()
    manifest = json.loads((WORK / "manifest.json").read_text(encoding="utf8"))
    if {name: sha(path) for name, path in index(SOURCE).items()} != manifest["files"]:
        raise ValueError("Prepared source changed after verification.")
    if preview is not None:
        preview = Path(preview).resolve(strict=True)
        if (
            preview.suffix.lower() not in (".png", ".jpg", ".jpeg")
            or preview.stat().st_size >= 1024 * 1024
        ):
            raise ValueError("Preview must be a JPG/PNG below 1 MiB.")
        with Image.open(preview) as image:
            if image.size != (512, 512):
                raise ValueError("This Toolkit expects a 512 by 512 preview.")
            image.verify()
    root = PROJECT / "local/Workshop-upload" / manifest["fix_revision"][:12]
    content = root / "content"
    if content.exists():
        raise ValueError(
            "Staging already exists; preserve its WorkshopID and choose/review an update instead of resetting it."
        )
    description = (PROJECT / "workshop/description.en.bbcode").read_text(encoding="utf8").strip()
    title = "HWMP Patch 2.4 - Field Test"
    workshop_id = workshop_item_id()
    if len(title) > 128 or len(description) > 8000:
        raise ValueError("Toolkit title/description limit exceeded.")
    shutil.copytree(SOURCE, content)
    if {name: sha(path) for name, path in index(content).items()} != manifest["files"]:
        raise RuntimeError("Staged source copy differs.")
    if preview is not None:
        preview_name = "preview.png" if preview.suffix.lower() == ".png" else "preview.jpg"
        shutil.copy2(preview, content / preview_name)
    config = (
        "Title: "
        + title
        + "\nTags: Balance Fixes Multiplayer\nGameType: HomeworldRM\nModType: MOD\n"
        "BigFilename: HWMPPatch24.big\nWorkshopID: "
        + workshop_id
        + "\nDescription:\n"
        + description
        + "\n"
    )
    (content / "config.txt").write_text(config, encoding="utf8", newline="\r\n")
    shutil.copy2(PROJECT / "workshop/description.ru.bbcode", root / "description.ru.bbcode")
    save(
        root / "preparation.json",
        {
            "identity": "HWMP-workshop-preparation-v1",
            "fix_revision": manifest["fix_revision"],
            "source_inventory": manifest["files"],
            "preview_sha256": sha(preview) if preview else None,
            "artwork_kind": "owner_review_pending",
            "description_characters": len(description),
            "content": str(content),
            "published": False,
            "workshop_id": workshop_id,
            "expected_operation": "create" if workshop_id == "0" else "update",
            "approval_required": "Show owner the exact description and preview before any create/update.",
        },
    )
    save(
        PROJECT / "local/workshop-latest.json",
        {"root": str(root), "content": str(content), "published": False},
    )
    return {
        "staged": str(content),
        "workshop_id": workshop_id,
        "expected_operation": "create" if workshop_id == "0" else "update",
        "runtime_files": len(manifest["files"]),
        "title": title,
        "description_characters": len(description),
        "preview_bytes": preview.stat().st_size if preview else None,
        "missing_preview": preview is None,
        "published": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.preview), indent=2))
