"""Create a pinned human test record. Does not run the game or mark tests passed."""

import argparse
from datetime import datetime, timezone
import json
from hwrm_common import PROJECT, save, sha
import install_hwmp24
from language_data import LANGUAGES


def create_run(language, candidate=False):
    if candidate:
        install_hwmp24.RELEASE = PROJECT / "local/HWMPPatch245-candidate"
    sums, version = install_hwmp24.release_files()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    plan = PROJECT / "autotests/manual-cases.ru.json"
    cases = json.loads(plan.read_text(encoding="utf8"))
    result = {
        "created_at_utc": stamp,
        "language": language,
        "plan_language": "Russian",
        "identity": version["identity"],
        "fix_revision": version["fix_revision"],
        "archives": {
            n: sums[n] for n in ("HWMPPatch24.big", *(language + ".big" for language in LANGUAGES))
        },
        "plan_sha256": sha(plan),
        "game_build": None,
        "tester": None,
        "map": "leveldata/multiplayer/deathmatchhw2/2p_jadeth.level",
        "actual_settings": None,
        "observations_are_human_supplied": True,
        "cases": [
            {
                **{k: v for k, v in case.items() if k != "variants"},
                "variant": variant,
                "status": "not_run",
                "observed": None,
                "evidence": [],
                "save_name": None,
            }
            for case in cases
            for variant in case["variants"]
        ],
    }
    folder = PROJECT / "local/native-tests" / stamp
    save(folder / "results.json", result)
    guide = PROJECT / (
        "docs/ru/NATIVE_TESTS.md" if language == "Russian" else "docs/NATIVE_TESTS.md"
    )
    (folder / "NATIVE_TESTS.md").write_bytes(guide.read_bytes())
    return folder / "results.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new-run", choices=LANGUAGES, required=True)
    parser.add_argument(
        "--candidate",
        action="store_true",
        help="Record the current verified candidate instead of the preserved ordinary release",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            {"results": str(create_run(args.new_run, args.candidate)), "game_launched": False}
        )
    )
