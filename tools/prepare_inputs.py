"""Extract local native inputs with the official Archive tool; never run a game."""

import json
import subprocess
from pathlib import Path
from hwrm_common import (
    PROJECT,
    CACHE,
    DONOR,
    RUSSIAN_STOCK,
    ARCHIVE,
    DONOR_SHA,
    GAME,
    TOOL,
    SETTINGS,
    index,
    sha,
    save,
    short_path,
)


def extract(archive, target):
    target = Path(target).resolve()
    assert target.is_relative_to(CACHE.resolve())
    if target.exists() and any(target.iterdir()):
        return
    target.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [str(TOOL), "-a", str(archive), "-e", short_path(target)], capture_output=True, text=True
    )
    assert result.returncode == 0, ("Extraction failed", archive, result.returncode)


def prepare(economy=False):
    assert (
        ARCHIVE.is_file() and sha(ARCHIVE) == DONOR_SHA
    ), "Supply the pinned Test21 archive through local/settings.json."
    extract(ARCHIVE, DONOR)
    expected = {
        row["path"]: row["sha256"]
        for row in json.loads((PROJECT / "baseline/test-inventory.json").read_text())["inventory"]
    }
    assert {n: sha(p) for n, p in index(DONOR).items()} == expected, "The extracted donor differs."
    from language_data import LANGUAGES, stock_directory, verify_native_input

    for language in LANGUAGES:
        extract(verify_native_input(language), stock_directory(language))
    assert any(RUSSIAN_STOCK.glob("*.ucs")), "Stock Russian UCS files are missing."
    for archive_name, folder in (
        ("Homeworld2.big", "rm-base"),
        ("HW2Ships.big", "rm-hw2"),
        ("HW1Ships.big", "rm-hw1"),
        ("HW1Campaign.big", "rm-campaign-hw1"),
        ("HW2Campaign.big", "rm-campaign-hw2"),
    ):
        extract(GAME / "HomeworldRM/Data" / archive_name, CACHE / "players-patch-audit" / folder)
    if economy:
        extract(
            Path(
                SETTINGS.get("classic_archive", str(GAME / "Homeworld2Classic/Data/Homeworld2.big"))
            ),
            CACHE / "players-patch-audit/classic",
        )
        extract(
            Path(
                SETTINGS.get(
                    "regular_archive",
                    str(
                        GAME
                        / "HomeworldRM/DataWorkshopMODs/76561198011852645/1190476337/2.3PlayersPatch.big"
                    ),
                )
            ),
            CACHE / "players-patch-audit/regular",
        )
        extract(GAME / "HomeworldRM/DataUpdates/DataMP.big", CACHE / "players-patch-audit/rm-mp")
    from production_data import catalog

    catalog()  # Reject stale or changed inherited native definitions.
    report = {
        "status": "passed",
        "donor_sha256": DONOR_SHA,
        "files": len(expected),
        "asset_cache": str(CACHE),
        "game_launched": False,
    }
    save(PROJECT / "local/inputs.json", report)
    print(json.dumps(report))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--economy", action="store_true")
    args = parser.parse_args()
    prepare(args.economy)
