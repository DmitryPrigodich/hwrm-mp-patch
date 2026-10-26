"""Private native callback trace, forced stationary Dock under real fire."""

import re


def prepare(put, clone_ship, native):
    core = native["scripts/playerspatch/ships_util/core/global.lua"].read_text(encoding="ascii")
    match = re.search(
        r"(?m)^HWMP_DockStalls =.*?(?=^function SobGroup_AnyBeingCaptured)", core, re.S
    )
    assert match
    helper = (
        match[0]
        .replace("HWMP_DockStalls", "HWJ_Stalls")
        .replace("SobGroup_UnderAttackReissueDock", "HWJ_ReissueDock")
    )
    helper = helper.replace(
        "SobGroup_DockSobGroupWithAny(group)",
        'HWJ_Log(group,"retry",now,ship_id)\n        SobGroup_DockSobGroupWithAny(group)',
    )
    helper = re.sub(
        r"function HWJ_ReissueDock\(group(?:, ship_id)?\)",
        lambda m: m[0] + '\n    HWJ_Log(group,"callback",Universe_GameTime(),ship_id)',
        helper,
    )
    prefix = """dofilepath("data:scripts/hwmp24/autotests/run.lua")
dofilepath("data:scripts/hwmp24/autotests/dock_cases.lua")
function HWJ_Log(group,event,now,ship_id)
    for i=1,getn(HWJ_CASES) do
        local c=HWJ_CASES[i]
        if SobGroup_Empty(group)==0 and SobGroup_GroupInGroup(group,c.target)==1 and SobGroup_GroupInGroup(c.target,group)==1 then
            print("HWMP_AUTO|v=1|run="..HWA_RUN.."|mode=DockStall|case="..c.id.."|t="..now.."|event=dock_"..event.."|ship_id="..(ship_id or -1).."|order="..SobGroup_GetCurrentOrder(group).."|under_attack="..SobGroup_UnderAttack(group).."|actual_speed="..SobGroup_GetActualSpeed(group).."|can_move="..SobGroup_CanDoAbility(group,AB_Move).."|can_dock="..SobGroup_CanDoAbility(group,AB_Dock).."|docked="..SobGroup_IsDocked(group))
        end
    end
end
"""
    for race, label in [("hgn", "Hgn"), ("vgr", "Vgr")]:
        original = race + "_interceptor"
        private = "hwa_dock_" + race
        text = (
            prefix
            + helper
            + "\nfunction HWJ_Update_"
            + label
            + "(group,playerIndex,shipID)\n HWJ_ReissueDock(group,shipID)\nend"
        )
        path = f"ship/{private}/{private}.lua"
        put(path, text)

        def transform(s, path=path, label=label):
            s = re.sub(r"^StartShipWeaponConfig\([^\n]+\);?\s*$", "", s, flags=re.M)
            s = re.sub(r"^NewShipType.maxhealth=.*$", "NewShipType.maxhealth=100000", s, flags=re.M)
            s, n = re.subn(
                r"data:ship/" + label + r"_Interceptor/" + label + r"_Interceptor.lua",
                "data:" + path,
                s,
                flags=re.I,
            )
            assert n == 1
            s = s.replace('"Update_' + label + '_Interceptor"', '"HWJ_Update_' + label + '"')
            return s

        clone_ship(original, private, transform)


def cases(add, volumes):
    result = []
    for race, owner, enemy in [("hgn", 0, 1), ("vgr", 1, 0)]:
        for action in ("stall", "moving", "forbidden", "move_order", "idle"):
            k = len(result)
            x = -100000 + k % 5 * 45000
            z = -20000 + k // 5 * 110000
            name = "dockstall_" + race + "_" + action
            carrier = add(name + "_carrier", race + "_carrier", [x, 0, z - 5500], owner)
            target = add(name + "_target", "hwa_dock_" + race, [x, 0, z], owner, 0)
            source = add(name + "_enemy", "hgn_assaultfrigate", [x + 500, 0, z + 500], enemy)
            destination = name + "_move"
            volumes.append([destination, [x + 10000, 0, z], 100])
            result.append(
                dict(
                    id=name,
                    kind="dock_stall",
                    race=race,
                    player=owner,
                    enemy=enemy,
                    action=action,
                    target=target,
                    carrier=carrier,
                    source=source,
                    destination=destination,
                    x=x,
                    z=z,
                )
            )
    return result
