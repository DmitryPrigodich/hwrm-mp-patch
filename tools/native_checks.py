"""Create a pinned human test record. Does not run the game or mark tests passed."""

import argparse
from datetime import datetime, timezone
import json
from hwrm_common import PROJECT, save, sha
from install_hwmp24 import release_files
from language_data import LANGUAGES


def create_run(language):
    sums, version = release_files()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    plan = PROJECT / "docs/native-test-cases.json"
    cases = json.loads(plan.read_text(encoding="utf8"))
    result = {
        "created_at_utc": stamp,
        "language": language,
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
    (folder / "NATIVE_TESTS.md").write_bytes((PROJECT / "docs/NATIVE_TESTS.md").read_bytes())
    return folder / "results.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new-run", choices=LANGUAGES, required=True)
    args = parser.parse_args()
    print(json.dumps({"results": str(create_run(args.new_run)), "game_launched": False}))
