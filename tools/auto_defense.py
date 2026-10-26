"""Private native missile-defense fixtures; never change the shipped fighter."""

import re


def prepare(put, clone_ship, native, donor):
    weapon = native["weapon/tai_defenselaser/tai_defenselaser.wepn"].read_text(encoding="ascii")
    old = 'AddWeaponResult(NewWeaponType,"Hit","DamageHealth","Target",10,10,"");'
    assert weapon.count(old) == 1
    put(
        "weapon/hwa_df_observer/hwa_df_observer.wepn",
        weapon.replace(old, old.replace("10,10", "0,0")),
    )
    for variant in ("control", "applied", "trace"):
        source = (
            (donor / "ship/tai_defensefighter/tai_defensefighter.lua")
            if variant == "control"
            else native["ship/tai_defensefighter/tai_defensefighter.lua"]
        )
        text = source.read_text(encoding="ascii")
        functions = re.findall(r"(?m)^function (\w+)\(", text)
        for name in sorted(functions, key=len, reverse=True):
            text = re.sub(r"\b" + name + r"\b", "HWD_" + variant + "_" + name, text)
        cache = "HWD_" + variant + "_missile_counts"
        text = text.replace("defenseFighterMissileTargets", cache)
        anchor = 'local numberEnemyMissiles = Selection_GetMissiles("AllMissiles")'
        assert text.count(anchor) == 1
        text = text.replace(
            anchor,
            anchor
            + '\n    HWD_Trace("scan",CustomGroup,playerID,shipID,"global_missiles="..numberEnemyMissiles.."|previous_count="..tostring('
            + cache
            + "[shipID]))",
        )
        anchor = 'SobGroup_AttackSelection(playerID, CustomGroup, "IncomingMissiles", 1)'
        assert text.count(anchor) > 0
        text = text.replace(
            anchor,
            'HWD_Trace("attack_selection",CustomGroup,playerID,shipID,"selection=IncomingMissiles")\n        '
            + anchor,
        )
        name = "HWD_" + variant + "_updateDefenseFighter"
        anchor = "function " + name + "(CustomGroup, playerID, shipID)"
        assert text.count(anchor) == 1
        text = text.replace(
            anchor, anchor + '\n    HWD_Trace("callback",CustomGroup,playerID,shipID,"")'
        )
        text = 'dofilepath("data:scripts/hwmp24/autotests/defense.lua")\n' + text
        private = "hwa_df_" + variant
        path = f"ship/{private}/{private}.lua"
        put(path, text)

        def transform(s, path=path, name=name, variant=variant):
            s, n = re.subn(
                "data:ship/tai_defensefighter/tai_defensefighter.lua", "data:" + path, s, flags=re.I
            )
            assert n == 1
            assert s.count('"updateDefenseFighter"') == 1
            s = s.replace('"updateDefenseFighter"', '"' + name + '"')
            assert s.count('"Tai_DefenseLaser"') == 1
            return s if variant == "trace" else s.replace('"Tai_DefenseLaser"', '"hwa_df_observer"')

        clone_ship("tai_defensefighter", private, transform)


def cases(add, mode="Defense"):
    result = []

    def create(tag, action, variant, ammo="hmf", source_owner=1, rep=1):
        index = len(result) + 1
        x = -100000 + ((index - 1) % 6) * 35000
        z = -100000 + ((index - 1) // 6) * 50000
        c = {
            "Defense": "df_",
            "DefenseIdentity": "di_",
            "DefenseOrders": "do_",
            "DefenseIntercept": "dr_",
        }[mode] + tag
        protected = mode == "DefenseIntercept"
        guard = add(c + "_guard", "hwa_probe_medium", [x, 0, z - 2000 if protected else z], 5)
        far = action == "far"
        target = (
            guard
            if protected
            else add(c + "_target", "hwa_probe_medium", [x, 0, z + (12000 if far else -2000)], 0)
        )
        source = add(
            c + "_source", "hwa_launcher_" + ammo, [x, 0, z + (8500 if far else 1500)], source_owner
        )
        source2 = add(
            c + "_source2",
            "hwa_launcher_" + ammo,
            [x + 200, 0, z + (8500 if far else 1500)],
            source_owner,
        )
        defender = ""
        if variant != "none":
            ship = "tai_defensefighter" if variant == "stock" else "hwa_df_" + variant
            defender = add(c + "_defender", ship, [x, 0, z + (-1800 if protected else 100)], 5)
        result.append(
            {
                "id": c,
                "mode": mode,
                "kind": "defense",
                "index": index,
                "action": action,
                "variant": variant,
                "ammo": ammo,
                "source": source,
                "source2": source2,
                "source_player": source_owner,
                "guard": guard,
                "target": target,
                "defender": defender,
                "volley": 2 if ammo == "hmf" else 4,
                "old_selection": c + "_old_selection",
                "phase_group": c + "_phase2",
                "rep": rep,
                "attack_flag": 0,
                "x": x,
                "z": z,
            }
        )

    if mode == "DefenseOrders":
        for flag in (0, 1):
            create("missile_order_flag" + str(flag), "attack_order", "trace")
            result[-1]["attack_flag"] = flag
    else:
        if mode == "Defense":
            for action, owner in (("enemy", 1), ("ally", 3), ("own", 5), ("far", 1)):
                create(action, action, "applied", source_owner=owner)
        if mode in ("Defense", "DefenseIdentity"):
            for variant in ("control", "applied"):
                create("same_" + variant, "same_count", variant)
        if mode in ("Defense", "DefenseIntercept"):
            for ammo in ("hmf", "dd"):
                for rep in range(1, 4):
                    for variant in ("none", "stock"):
                        create(
                            f"intercept_{ammo}_{variant}_r{rep}",
                            "intercept",
                            variant,
                            ammo,
                            rep=rep,
                        )
    return result
