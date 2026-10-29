"""Cold callback dependency order and regeneration gates; native checks separate."""

from lupa.lua51 import LuaRuntime

from hwmp24 import SOURCE
from verify_hwmp24 import inspect_lua


def verify():
    memory_path = "scripts/playerspatch/ships_util/core/memgroup.lua"
    callbacks = [f"ship/{ship}/{ship}.lua" for ship in ("kus_cloakedfighter", "kus_dronefrigate")]
    for order in (callbacks, list(reversed(callbacks))):
        vm = LuaRuntime(register_eval=False, register_builtins=False)
        g = vm.globals()
        g.print = lambda *a: None

        def load(name):
            assert name.startswith("data:")
            vm.execute(inspect_lua((SOURCE / name[5:]).read_text(encoding="ascii")))

        g.dofilepath = load
        assert g.MemGroup is None
        for path in order:
            load("data:" + path)
        g.Create_Kus_CloakedFighter("fighter", 0, 17)
        vm.execute("CF_MEM:set(99, {sentinel = 73})")
        load("data:" + memory_path)
        load("data:" + callbacks[0])
        vm.execute('assert(MemGroup.Get("cloaked_fighters"):get(99).sentinel == 73)')
        state = {"hp": 0.5, "dock": 0, "space": 1, "speed": 0}
        healed = []

        def group(value):
            assert value == "fighter", value

        def read(key):
            def query(value):
                group(value)
                return state[key]

            return query

        def heal(value, hp):
            group(value)
            healed.append(hp)

        g.SobGroup_HealthPercentage = read("hp")
        g.SobGroup_IsDocked = read("dock")
        g.SobGroup_AreAllInRealSpace = read("space")
        g.SobGroup_GetActualSpeed = read("speed")
        g.SobGroup_SetHealth = heal
        update = lambda: g.Update_Kus_CloakedFighter("fighter", 0, 17)
        update()
        for key, value in (("dock", 1), ("space", 0), ("speed", 20)):
            old = state[key]
            state[key] = value
            update()
            assert not healed, (key, healed)
            state[key] = old
        update()
        assert healed == [0.516]
        healed.clear()
        state["hp"] = 0.4
        update()
        for i in range(19):
            update()
        assert not healed, "Damage must retain the original 20-tick combat window"
        update()
        assert healed == [0.41600000000000004] or abs(healed[0] - 0.416) < 1e-12
        healed.clear()
        state["hp"] = 1
        update()
        assert not healed
        g.Destroy_Kus_CloakedFighter("fighter", 0, 17)
        vm.execute("assert(CF_MEM:get(17) == nil)")
    return {
        "status": "passed",
        "orders": 2,
        "registry_survives_reload": True,
        "regeneration_gates": "dock/realspace/speed/damage window/full health",
        "native_engine_tested": False,
    }


if __name__ == "__main__":
    print(verify())
