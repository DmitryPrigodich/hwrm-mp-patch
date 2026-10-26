"""Native salvage completion/interruption with concurrent idle callback controls."""

import re


def prepare(put, clone_ship, native):
    source = """dofilepath("data:scripts/hwmp24/autotests/run.lua")
dofilepath("data:scripts/hwmp24/autotests/salvage_cases.lua")
HWS_TraceCases=HWS_TraceCases or {}
function HWS_TraceUpdate(group,playerIndex,shipID)
    local before=SobGroup_CanDoAbility(group,AB_Scuttle)
    SobGroup_NoSalvageScuttle(group,playerIndex,shipID)
    local baseline=-1
    local record=HWMP_FindEffectRecord(group,0)
    if record and record.abilities[AB_Scuttle] then baseline=record.abilities[AB_Scuttle].baseline end
    if HWS_TraceCases[shipID]==nil then
        for i=1,getn(HWS_CASES) do
            local c=HWS_CASES[i]
            SobGroup_CreateIfNotExist(c.target)
            if SobGroup_Count(group)>0 and SobGroup_GroupInGroup(group,c.target)==1 then HWS_TraceCases[shipID]=c;break end
        end
    end
    local c=HWS_TraceCases[shipID]
    if c then print("HWMP_AUTO|v=1|run="..HWA_RUN.."|mode="..c.mode.."|case="..c.id.."|t="..Universe_GameTime().."|event=salvage_callback|group="..group.."|ship_id="..shipID.."|before="..before.."|after="..SobGroup_CanDoAbility(group,AB_Scuttle).."|docking="..SobGroup_IsDoingAbility(group,AB_Dock).."|baseline="..baseline.."|owner="..SobGroup_GetPlayerOwner(group)) end
end
"""
    private = "hwa_salvage_probe"
    path = f"ship/{private}/{private}.lua"
    put(path, source)

    def transform(s):
        s = re.sub(r"^StartShipWeaponConfig\([^\n]+\);?\s*$", "", s, flags=re.M)
        s = re.sub(r'^StartShipHardPointConfig\([^\n]*,"Weapon",[^\n]+\);?\s*$', "", s, flags=re.M)
        s = re.sub(r"^NewShipType.maxhealth=.*$", "NewShipType.maxhealth=100000", s, flags=re.M)
        s, n = re.subn(
            r"data:ship/Hgn_TorpedoFrigate/Hgn_TorpedoFrigate.lua", "data:" + path, s, flags=re.I
        )
        assert n == 1
        return s.replace('"Update_Hgn_TorpedoFrigate"', '"HWS_TraceUpdate"')

    clone_ship("hgn_torpedofrigate", private, transform)


def cases(add, volumes, mode="Salvage"):
    result = []
    for race, owner, enemy in [("kus", 4, 1), ("tai", 5, 0)]:
        for action in ("complete", "stop", "destroy"):
            k = len(result)
            x = -90000 + k % 3 * 80000
            z = -40000 + k // 3 * 110000
            name = (
                ("salvage_banned_" if mode == "SalvageBaselines" else "salvage_")
                + race
                + "_"
                + action
            )
            target = add(name + "_target", "hwa_salvage_probe", [x, 0, z], enemy)
            mother = add(name + "_mother", race + "_mothership", [x, 0, z - 4500], owner)
            actors = [
                add(
                    name + "_s" + str(i),
                    race + "_salvagecorvette",
                    [x + i * 250 - 375, 0, z + 600],
                    owner,
                )
                for i in (1, 2)
            ]
            idle = add(name + "_idle", "hwa_salvage_probe", [x + 12000, 0, z], enemy)
            result.append(
                dict(
                    id=name,
                    kind="salvage",
                    mode=mode,
                    race=race,
                    owner=owner,
                    enemy=enemy,
                    action=action,
                    pre_scuttle=0 if mode == "SalvageBaselines" else 1,
                    target=target,
                    mother=mother,
                    actors=actors,
                    idle=idle,
                    x=x,
                    z=z,
                )
            )
    return result
