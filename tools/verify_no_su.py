"""Release acceptance: no SU rules, prices, HUD or supply mutations remain."""

from tool_safety import ensure_normal_python

ensure_normal_python()
import json
import subprocess
from hwrm_common import PROJECT, CACHE, index, sha
from hwrm_inspect import record_config
from production_data import stock_files


def verify(source):
    files = index(source)
    forbidden = [name for name in files if "cataclysm" in name or "support_units" in name]
    assert not forbidden, forbidden
    for name, path in files.items():
        if path.suffix.lower() in (".lua", ".ship"):
            text = path.read_text(encoding="utf-8-sig")
            assert not any(
                word in text
                for word in ("HWMP_Cataclysm", "HWMP_SupportUnits", "HWMP_SU246", "HWMP_SURow")
            ), name
    # Compare full configuration/call streams to the pre-SU native race definitions.
    from hwrm_common import DONOR

    inherited = stock_files()
    inherited.update(index(DONOR))
    design = json.loads((PROJECT / "design/cataclysm.json").read_text(encoding="utf8"))
    for ident in design["ships"]:
        name = f"ship/{ident}/{ident}.ship"
        assert record_config(files[name].read_text(encoding="utf-8-sig")) == record_config(
            inherited[name].read_text(encoding="utf-8-sig")
        ), ident
    # Preserve ALL classic caps, including the combat class limits removed by Cataclysm.
    caps = [name for name in files if "/unitcaps/" in name and name.endswith(".lua")]
    for name in caps:
        if name in inherited:
            assert files[name].read_bytes() == inherited[name].read_bytes(), name
    compiler = CACHE / "hwmp-testgrounds-step/lua4/lua-4.0.1/luac4-x86.exe"
    parsed = 0
    ship_paths = {f"ship/{ident}/{ident}.ship" for ident in design["ships"]}
    changed = {
        name
        for name, path in files.items()
        if name not in inherited or sha(path) != sha(inherited[name])
    }
    for name, path in files.items():
        if name not in changed and name not in ship_paths:
            continue
        if path.suffix.lower() not in (
            ".lua",
            ".ship",
            ".wepn",
            ".subs",
            ".miss",
            ".wf",
            ".resource",
        ):
            continue
        result = subprocess.run([str(compiler), "-p", str(path)], capture_output=True, text=True)
        assert result.returncode == 0, (name, result.stdout, result.stderr)
        parsed += 1
    return {
        "status": "passed",
        "su_enabled": False,
        "original_ship_types": len(design["ships"]),
        "classic_cap_files": len(caps),
        "lua4_parsed": parsed,
        "engine_tested": False,
    }
