"""Parse diagnostic log observations without declaring native test passes."""

import argparse
import json
from pathlib import Path
from hwrm_common import PROJECT, save, sha


def collect(log, revision):
    runs = []
    current = None
    for number, line in enumerate(
        Path(log).read_text(encoding="utf8", errors="replace").splitlines(), 1
    ):
        start = line.find("HWMP_TEST|")
        if start < 0:
            continue
        fields = {}
        for item in line[start + 10 :].split("|"):
            key, sep, value = item.partition("=")
            if sep:
                if key in fields:
                    raise ValueError(f"Duplicate field at log line {number}: {key}")
                fields[key] = value.strip()
        if fields.get("v") != "1":
            raise ValueError("Unsupported log schema")
        if fields.get("suite") != revision:
            raise ValueError("Log does not match the prepared testground revision")
        if fields.get("mission") not in ("gravity", "assault", "missiles"):
            raise ValueError("Unknown mission")
        fields["log_line"] = number
        fields["t"] = float(fields["t"])
        if fields.get("event") == "init":
            current = {
                "mission": fields["mission"],
                "events": [],
                "finished": False,
                "native_verdict": "not_evaluated",
            }
            runs.append(current)
        if current is None or fields["mission"] != current["mission"]:
            raise ValueError("Missing mission init record")
        if current["events"] and fields["t"] < current["events"][-1]["t"]:
            # Save/load can legitimately rewind game time; preserve and label it.
            current.setdefault("time_rewinds", []).append(number)
        current["events"].append(fields)
        if fields.get("event") == "finished":
            current["finished"] = True
    if not runs:
        raise ValueError("No testground init records in log")
    for run in runs:
        run["samples"] = sum(e.get("event") == "sample" for e in run["events"])
        run["manual_markers"] = sum(e.get("event") == "manual_marker" for e in run["events"])
        run["state"] = "finished_observation" if run["finished"] else "partial_observation"
    return {
        "schema": 1,
        "revision": revision,
        "log_sha256": sha(Path(log)),
        "provenance": "unverified_log",
        "status": "observation_only",
        "runs": runs,
        "native_test_plan_updated": False,
        "physical_hull_count_inferred": False,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    version = json.loads((PROJECT / "local/testgrounds/release.json").read_text(encoding="utf8"))
    report = collect(args.log, version["revision"])
    # Require a local JSON destination and preserve the input log.
    dest = args.output.resolve()
    if (
        dest == args.log.resolve()
        or dest.suffix.lower() != ".json"
        or not dest.is_relative_to((PROJECT / "local").resolve())
    ):
        raise ValueError("Write observations as a JSON inside this repository local directory")
    save(dest, report)
    print(json.dumps({k: v for k, v in report.items() if k != "runs"}, indent=2))
