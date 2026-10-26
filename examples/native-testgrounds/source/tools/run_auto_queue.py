"""Sequential native suite runner; refuses stale evidence and leaves healthy timeouts open."""

import argparse
import json
import time

from run_auto_tests import launch, collect, status, MODES, stage_auto_checkpoint

p = argparse.ArgumentParser()
p.add_argument("modes", nargs="+", choices=MODES)
p.add_argument("--wall-timeout", type=float, default=600)
a = p.parse_args()
for mode in a.modes:
    started = launch(mode)
    print(json.dumps(started), flush=True)
    if mode in ("SaveLoadAuto", "SaveLoadTrace", "SaveLoadEmpty", "SaveLoadCoop"):
        print(json.dumps(stage_auto_checkpoint()), flush=True)
    deadline = time.monotonic() + a.wall_timeout
    while True:
        _, report, _, _ = status()
        if report["status"] in ("finished", "fatal_error", "process_exited"):
            print(json.dumps(collect(close=True)), flush=True)
            if report["status"] != "finished" or report["errors"]:
                raise SystemExit("Queue halted on native error; collected the owned process")
            break
        if time.monotonic() >= deadline:
            print(json.dumps(collect()), flush=True)
            raise SystemExit("Queue timeout; healthy unfinished process remains open")
        time.sleep(2)
