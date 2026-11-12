"""Meaningful boundary/ownership fixtures for the isolated prototype, not engine tests."""

from tool_safety import ensure_normal_python

ensure_normal_python()

import subprocess

from lupa.lua51 import LuaRuntime
from cataclysm import FAMILY
from cataclysm_descriptions import description_ids
from hwrm_common import CACHE, index, sha
from hwrm_inspect import plain, record_config


def verify(source, inputs, design, config):
    from cataclysm246_candidate import PROFILES, RULE_NAME

    files = index(source)
    callbacks = "scripts/rules/deathmatch/deathmatch.lua"
    assert files[callbacks].read_text() == inputs[callbacks].read_text().replace(
        'GameRulesName == "HWMP 2.4.5 Cataclysm"', f'GameRulesName == "{RULE_NAME}"'
    )
    for ident, row in design["ships"].items():
        name = f"ship/{ident}/{ident}.ship"
        old = inputs[name].read_text(encoding="ascii")
        new = files[name].read_text(encoding="ascii")
        assert record_config(old) == record_config(new), (
            "Ordinary branch changed",
            ident,
        )
        before, calls = record_config(old, rule_props={"hwmp_cataclysm": 1})
        after, new_calls = record_config(new, rule_props={"hwmp_cataclysm": 1})
        assert before == after, ident
        expected = [
            (
                func,
                [FAMILY, 0] if func == "setSupplyValue" and args[0] == FAMILY else args,
            )
            for func, args in calls
        ]
        assert new_calls == expected, ident
        assert row["su_per_group"] == row["su_per_hull"] * row["build_batch"]

    menu = LuaRuntime()
    menu.globals().dofilepath = lambda *_: None
    menu.execute(files["scripts/rules/hwmpcataclysm.lua"].read_text(encoding="ascii"))
    assert menu.globals().GameRulesName == RULE_NAME
    options = plain(menu.globals().GameSetupOptions)
    caps = next(row for row in options.values() if row["name"] == "unitcaps")
    assert caps["visible"] == 0 and caps["default"] == 0
    assert caps["choices"] == {1: "Fixed SU", 2: "Normal"}
    for race in design["races"]:
        normal = files[f"scripts/races/{race}/hwmp_cataclysm/unitcaps/normal.lua"].read_text()
        assert normal.endswith(
            f'supplyLimit("Carrier", {config["carrier_caps"][race]})\nsupplyLimit("Shipyard", 1)\n'
        )
        for profile in PROFILES:
            assert (
                files[f"scripts/races/{race}/hwmp_cataclysm/unitcaps/{profile}.lua"].read_text()
                == normal
            )
            assert (
                files[f"scripts/rules/hwmpcataclysm/unitcaps/{profile}.lua"].read_text()
                == files["scripts/rules/hwmpcataclysm/unitcaps/normal.lua"].read_text()
            )

    lua = LuaRuntime(register_eval=False, register_builtins=False)
    lua.execute("""
        getn = table.getn; strlower = string.lower; gsub = string.gsub; strfind = string.find
        counts = {[0]={}, [1]={}}; restrictions = {[0]={}, [1]={}}
        policies = {[0]={}, [1]={}}; settings = {nocruisers=0, strikecraftgamemode=0, carriersonly=0, research=1}
        labels = {}; mutations = 0; rule_adds = 0; active_rules = {}
        function Universe_PlayerCount() return 2 end
        function Universe_CurrentPlayer() return 0 end
        function Player_IsAlive(p) return 1 end
        function Player_GetLevelOfDifficulty(p) return 1 end
        function PlayerRace_GetString(p,k,default) return policies[p][k] or default end
        function GetGameSettingAsNumber(k) return settings[k] or 0 end
        function Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(p,s) return counts[p][s] or 0 end
        function Player_BuildOptionIsRestricted(p,s) return restrictions[p][s] or 0 end
        function Player_RestrictBuildOption(p,s) restrictions[p][s]=1; mutations=mutations+1 end
        function Player_UnrestrictBuildOption(p,s) restrictions[p][s]=0; mutations=mutations+1 end
        function UI_SetTextLabelText(screen,element,value) labels[table.getn(labels)+1]=value end
        function UI_SetElementVisible(...) end
        function Rule_Exists(name) return active_rules[name] or 0 end
        function Rule_AddInterval(name,interval) active_rules[name]=1; rule_adds=rule_adds+1; assert(interval==0.5) end
        function print(...) end
    """)
    lua.execute(files["scripts/hwmp24/cataclysm_hud.lua"].read_text(encoding="ascii"))
    g = lua.globals()
    cases = []

    def fleet(name, counts, expected, player=0):
        g.counts[player] = lua.table_from(counts)
        assert g.HWMP_SU246Snapshot(player) == expected, (
            name,
            g.HWMP_SU246Snapshot(player),
            expected,
        )
        g.HWMP_SU246Update()
        cases.append(name)

    fleet("Mothership only", {"hgn_mothership": 1}, (0, 300))
    fleet(
        "Starting economy",
        {"hgn_mothership": 1, "hgn_resourcecollector": 6, "hgn_resourcecontroller": 1},
        (22, 300),
    )
    fleet(
        "Hiigaran maximum",
        {"hgn_mothership": 1, "hgn_shipyard": 1, "hgn_carrier": 4},
        (210, 1300),
    )
    fleet(
        "Vaygr maximum",
        {"vgr_mothership": 1, "vgr_shipyard": 1, "vgr_carrier": 6},
        (290, 1300),
    )
    for prefix in ("kus", "tai"):
        fleet(
            prefix + " maximum",
            {prefix + "_mothership": 1, prefix + "_carrier": 4},
            (160, 1300),
        )
    fleet(
        "Clamped captured suppliers",
        {"hgn_mothership": 3, "hgn_shipyard": 3, "vgr_carrier": 9},
        (510, 1300),
    )
    fleet(
        "Exact fit",
        {
            "hgn_mothership": 1,
            "hgn_battlecruiser": 1,
            "hgn_destroyer": 1,
            "hgn_resourcecollector": 27,
        },
        (284, 300),
    )
    # 16 available: a 15-SU squadron fits; then 14 available does not.
    assert g.restrictions[0]["hgn_interceptor"] != 1
    g.counts[0]["hgn_resourcecollector"] = 28
    assert g.HWMP_SU246Snapshot(0) == (286, 300)
    g.HWMP_SU246Update()
    assert g.restrictions[0]["hgn_interceptor"] == 1
    cases.append("One SU short blocks")
    # Odd costs make a genuine exact 15-SU gap.
    fleet(
        "Exact 15 available",
        {
            "hgn_mothership": 1,
            "hgn_battlecruiser": 1,
            "hgn_destroyer": 1,
            "hgn_ioncannonfrigate": 1,
            "hgn_resourcecollector": 20,
        },
        (285, 300),
    )
    assert g.restrictions[0]["hgn_interceptor"] != 1
    fleet("Full", {"hgn_mothership": 1, "hgn_battlecruiser": 2}, (300, 300))
    assert g.restrictions[0]["hgn_interceptor"] == 1
    assert g.restrictions[0]["hgn_probe"] != 1
    fleet("Supplier loss over budget", {"hgn_battlecruiser": 2}, (300, 0))
    assert g.restrictions[0]["hgn_resourcecollector"] == 1
    fleet(
        "Supplier return unlocks",
        {"hgn_mothership": 1, "hgn_carrier": 1, "hgn_battlecruiser": 2},
        (340, 450),
    )
    assert g.restrictions[0]["hgn_resourcecollector"] != 1
    fleet(
        "Independent player",
        {"tai_mothership": 1, "tai_carrier": 1},
        (40, 550),
        player=1,
    )
    assert g.HWMP_SU246Snapshot(0) == (340, 450)
    # Existing foreign restrictions are never claimed/released by our gate.
    g.restrictions[0]["hgn_interceptor"] = 1
    g.HWMP_SU246OwnedLocks[0]["hgn_interceptor"] = None
    fleet(
        "External restriction while full",
        {"hgn_mothership": 1, "hgn_battlecruiser": 2},
        (300, 300),
    )
    fleet(
        "External restriction preserved on capacity gain",
        {"hgn_mothership": 1, "hgn_carrier": 1},
        (40, 450),
    )
    assert g.restrictions[0]["hgn_interceptor"] == 1
    # A delayed stock policy applied while our restriction exists must win on release.
    g.policies[0]["dm_nocruisers_build_restrict"] = "Hgn_Battlecruiser"
    g.settings["nocruisers"] = 1
    g.HWMP_SU246Policies[0] = None
    g.HWMP_SU246OwnedLocks[0]["hgn_battlecruiser"] = 1
    g.restrictions[0]["hgn_battlecruiser"] = 1
    g.HWMP_SU246Update()
    assert g.restrictions[0]["hgn_battlecruiser"] == 1
    cases.append("Overlapping known stock policy preserved")
    before = g.mutations
    g.HWMP_SU246Update()
    assert g.mutations == before, "Unchanged frames must not repeat restrict/unrestrict calls"
    g.HWMP_CataclysmHUDStart()
    g.HWMP_CataclysmHUDStart()
    assert g.rule_adds == 1
    assert g.labels[len(g.labels)] == "40/450"
    cases += [
        "Idempotent unchanged tick",
        "Single timer after repeated start/load hook",
        "HUD uses dynamic capacity",
    ]

    ids = description_ids(design)
    dictionaries = []
    for path in source.glob("locale/*/hwmp24_cataclysm.ucs"):
        raw = path.read_bytes()
        assert raw.startswith(b"\xff\xfe")
        text = raw.decode("utf-16")
        assert "\n" not in text.replace("\r\n", "")
        ucs = dict(line.split("\t", 1) for line in text.splitlines())
        for ident, number in ids.items():
            assert ucs[str(number)].startswith(f'SU: {design["ships"][ident]["su_per_group"]} | ')
        for ident, value in config["capacity_providers"].items():
            assert ucs[str(ids[ident])].endswith(f" | +{value} SU")
        dictionaries.append(path.parent.name)
    assert len(dictionaries) == 6
    compiler = CACHE / "hwmp-testgrounds-step/lua4/lua-4.0.1/luac4-x86.exe"
    parsed = []
    for name, path in files.items():
        if sha(path) == sha(inputs[name]):
            continue
        if path.suffix.lower() not in (".lua", ".ship"):
            continue
        completed = subprocess.run([str(compiler), "-p", str(path)], capture_output=True, text=True)
        assert completed.returncode == 0, (name, completed.stdout, completed.stderr)
        parsed.append(name)
    return {
        "status": "passed",
        "ordinary_ships_checked": len(design["ships"]),
        "lua4_parsed_changed_files": len(parsed),
        "fixture_cases": cases,
        "languages": sorted(dictionaries),
        "native_engine_tested": False,
        "atomic_queue_reservations_verified": False,
    }
