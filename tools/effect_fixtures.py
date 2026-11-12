"""No game files: native API stand-ins plus generated effect/journal templates."""

from tool_safety import ensure_normal_python

ensure_normal_python()
from lupa.lua51 import LuaRuntime
from effect_journal import generate_effects


def vm_for_templates():
    from verify_hwmp24 import MOCK, inspect_lua

    vm = LuaRuntime(register_eval=False, register_builtins=False)
    vm.execute(MOCK)
    vm.execute(inspect_lua(generate_effects()))
    return vm, None
