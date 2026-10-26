function HWJ_Init(c)
    HWA_Freeze(c.carrier);SobGroup_AbilityActivate(c.carrier,AB_Move,1)
    SobGroup_SetROE(c.target,PassiveROE);SobGroup_AbilityActivate(c.target,AB_Attack,0)
    SobGroup_SetSpeed(c.target,0)
    SobGroup_SetROE(c.source,PassiveROE);SobGroup_SetSpeed(c.source,0)
    BreakAlliance(c.player,c.enemy);BreakAlliance(c.enemy,c.player)
    c.last_sample=-1;c.stalled_under_fire=0
end

function HWJ_Tick(c,t)
    if t>=3 and not c.started then
        c.started=1
        if c.action~="idle" then SobGroup_DockSobGroupAndStayDocked(c.target,c.carrier) end
        SobGroup_Attack(c.enemy,c.source,c.target)
        if c.action=="moving" then SobGroup_SetSpeed(c.target,1) end
        HWA_Log(c,"dock_stall_started","action="..c.action.."|native_fire=1|speed_zero_is_fixture=1")
    end
    if t>=6 and not c.modified then
        c.modified=1
        if c.action=="forbidden" then SobGroup_AbilityActivate(c.target,AB_Dock,0)
        elseif c.action=="move_order" then SobGroup_Move(c.player,c.target,c.destination) end
    end
    if SobGroup_GetCurrentOrder(c.target)==COMMAND_Dock and SobGroup_UnderAttack(c.target)==1 and SobGroup_GetActualSpeed(c.target)<1 then c.stalled_under_fire=c.stalled_under_fire+1 end
    if t>=22 and not c.released then
        c.released=1;SobGroup_SetSpeed(c.target,1)
        if c.action=="forbidden" then SobGroup_AbilityActivate(c.target,AB_Dock,1) end
        SobGroup_Stop(c.enemy,c.source);SobGroup_AbilityActivate(c.source,AB_Attack,0)
        HWA_Log(c,"fixture_stall_released","game_time="..t)
    end
    if t>=65 then
        local status="measured"
        if c.action=="stall" and c.stalled_under_fire==0 then status="blocked" end
        HWA_Result(c,status,"action="..c.action.."|stalled_under_fire_samples="..c.stalled_under_fire.."|docked="..SobGroup_IsDocked(c.target).."|order="..SobGroup_GetCurrentOrder(c.target).."|trace_required=1")
    elseif c.last_sample<0 or t-c.last_sample>=1 then
        c.last_sample=t
        HWA_Log(c,"dock_stall_sample","action="..c.action.."|order="..SobGroup_GetCurrentOrder(c.target).."|under_attack="..SobGroup_UnderAttack(c.target).."|speed="..SobGroup_GetActualSpeed(c.target).."|docked="..SobGroup_IsDocked(c.target).."|hp="..HWA_Hp(c.target))
    end
end
