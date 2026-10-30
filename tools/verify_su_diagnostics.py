"""Offline regressions: never touch or stop a real game process."""

import hashlib
import os
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

from hwrm_common import PROJECT
from su_boundary_tests import read_run_log, lua_errors


def verify():
    with tempfile.TemporaryDirectory(prefix="su-log-fixture-", dir=PROJECT / "local") as folder:
        path = Path(folder) / "HwRM.log"
        old = b"HWMP_SUB|world=Hgn_Auto|event=end|old=1\n"
        path.write_bytes(old)
        process = dict(
            started_ns=time.time_ns(), previous_log_sha256=hashlib.sha256(old).hexdigest()
        )
        # Touching an old completed log cannot make it belong to a new run.
        future = process["started_ns"] + 1_000_000_000
        os.utime(path, ns=(future, future))
        assert read_run_log(path, process)[1] is False
        # Changed text with a timestamp predating launch is also rejected.
        path.write_bytes(b"different old endpoint")
        os.utime(path, ns=(1, 1))
        assert read_run_log(path, process)[1] is False
        # Fresh content/time is accepted, with the hash of the SAME captured bytes.
        new = "HWMP_SUB|world=Hgn_Auto|event=setup|".encode("utf-16")
        path.write_bytes(new)
        os.utime(path, ns=(future, future))
        with patch(
            "su_boundary_tests.sha", side_effect=AssertionError("Do not re-read a moving log")
        ):
            text, fresh = read_run_log(path, process)
        assert fresh and "event=setup" in text
        assert read_run_log(path, {})[1] is False
        assert read_run_log(Path(folder) / "missing", process) == ("", False)
    from lupa.lua51 import LuaRuntime
    from verify_hwmp24 import inspect_lua

    vm = LuaRuntime(register_eval=False, register_builtins=False)
    vm.execute(inspect_lua((PROJECT / "autotests/su_boundary.lua").read_text(encoding="ascii")))
    vm.execute("""
        SUB_Auto=0; SUB_T0=0; SUB_World="fixture"; SUB_Cost=15
        function Universe_GameTime() return 10 end
        function SUB_Log() end
        function SUB_Used() return 1886 end
        fixtureRU=100000; fixtureCount=0
        function Player_GetRU() return fixtureRU end
        function Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping() return fixtureCount end
        function Player_HasQueuedBuild() return 1 end
        function SobGroup_IsBuilding() return 1 end
        SUB_Item="hgn_interceptor"
        SUB_Cases={{id="Under",player=1,builders={"A","B"},base_count=0,last="",max_building=0,max_delta=0,started=0,start_ru=100000}}
        SUB_Observe()
        assert(SUB_Cases[1].max_building==2 and SUB_Cases[1].started==0)
        fixtureRU=99950; SUB_Observe(); assert(SUB_Cases[1].started==1)
        SUB_Cases[1].started=0; fixtureRU=100000; fixtureCount=1
        SUB_Observe(); assert(SUB_Cases[1].started==1 and SUB_Cases[1].max_delta==1)
    """)
    for text in (
        "parameter: invalid number of arguments",
        "syntax error near end",
        "attempt to call nil",
    ):
        assert lua_errors(text)
    assert not lua_errors("HWMP_SUB|event=setup|")
    return dict(
        status="passed",
        checks="stale content, old timestamp, fresh UTF16, legacy/missing log, snapshot hash, Lua errors, waiting queues versus paid/completed production",
        native_game_launched=False,
    )


if __name__ == "__main__":
    import json

    print(json.dumps(verify()))
