-- Destroy every old journal anchor, then build new fields in the same process.
function HWY_Init(c)
    for p=0,Universe_PlayerCount()-1 do
        for q=0,Universe_PlayerCount()-1 do if p~=q then SetAlliance(p,q) end end
    end
    HWA_Freeze(c.target);SobGroup_AbilityActivate(c.target,AB_Move,1)
end
function HWY_Tick(c,t)
    if t>=2 and not c.on then c.on=1;SobGroup_CustomCommand(c.source) end
    if t>=4 and not c.checked then
        c.checked=1;c.first_blocked=SobGroup_CanDoAbility(c.target,AB_Move)==0 and 1 or 0
    end
    if t>=5 and not c.killed then
        c.killed=1;SobGroup_TakeDamage(c.source,1);SobGroup_TakeDamage(c.target,1)
    end
    if t>=8 and not c.created then
        c.created=1;c.next_source=c.id.."_new_source";c.next_target=c.id.."_new_target"
        SobGroup_CreateIfNotExist(c.next_source);SobGroup_CreateIfNotExist(c.next_target)
        SobGroup_SpawnNewShipInSobGroup(c.owner,c.race.."_gravwellgenerator",c.next_source,c.next_source,c.volume)
        SobGroup_SpawnNewShipInSobGroup(c.owner,c.race.."_interceptor",c.next_target,c.next_target,c.volume)
    end
    if t>=9 and not c.ready then
        c.ready=1;HWA_Freeze(c.next_target);SobGroup_AbilityActivate(c.next_target,AB_Move,1)
        SobGroup_SetSpeed(c.next_target,0.75);SobGroup_CustomCommand(c.next_source)
    end
    if t>=12 and not c.checked_new then
        c.checked_new=1;c.new_blocked=SobGroup_CanDoAbility(c.next_target,AB_Move)==0 and 1 or 0
        SobGroup_TakeDamage(c.next_source,1)
    end
    if t>=16 then
        local restored=SobGroup_CanDoAbility(c.next_target,AB_Move)==1 and SobGroup_CanDoAbility(c.next_target,AB_Attack)==0 and SobGroup_GetSpeed(c.next_target)==0.75
        local old_gone=SobGroup_Empty(c.source)==1 and SobGroup_Empty(c.target)==1
        local status="failed"
        if restored and old_gone and c.first_blocked==1 and c.new_blocked==1 then status="passed" end
        HWA_Result(c,status,"old_anchors_gone="..(old_gone and 1 or 0).."|first_blocked="..c.first_blocked.."|new_blocked="..c.new_blocked.."|restored="..(restored and 1 or 0))
    end
end
