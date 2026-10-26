-- Native-only defense fixtures and non-mutating trace around private callbacks.
dofilepath("data:scripts/hwmp24/autotests/run.lua")
dofilepath("data:scripts/hwmp24/autotests/defense_cases.lua")

function HWD_Log(c,event,fields)
    print("HWMP_AUTO|v=1|run="..HWA_RUN.."|mode="..c.mode.."|case="..c.id.."|t="..Universe_GameTime().."|event="..event.."|"..fields)
end

function HWD_Trace(event,g,p,id,fields)
    SobGroup_CreateIfNotExist("HWD_Active")
    if SobGroup_Empty("HWD_Active")==1 or SobGroup_GroupInGroup(g,"HWD_Active")==0 then return end
    for i=1,getn(HWD_CASES) do
        local c=HWD_CASES[i]
        if c.defender~="" then SobGroup_CreateIfNotExist(c.defender) end
        if c.defender~="" and SobGroup_GroupInGroup(g,c.defender)==1 then
            local phase=1
            if SobGroup_Count(c.phase_group)>0 then phase=2 end
            SobGroup_CreateIfNotExist("HWD_TraceShipTargets")
            SobGroup_Clear("HWD_TraceShipTargets")
            SobGroup_GetCommandTargets("HWD_TraceShipTargets",g,COMMAND_Attack)
            if event=="attack_selection" then
                Selection_Create("HWD_TraceSelected")
                local selected=Selection_FilterInclude("HWD_TraceSelected","IncomingMissiles","NearPoint",c.x..",0,"..c.z,"18000")
                fields=fields.."|selected_missiles="..selected
            end
            HWD_Log(c,"defense_"..event,"phase="..phase.."|ship_id="..id.."|order="..SobGroup_GetCurrentOrder(g).."|guarding="..SobGroup_IsGuardingSobGroup(g,c.guard).."|ship_attack_targets="..SobGroup_Count("HWD_TraceShipTargets").."|"..fields)
            return
        end
    end
end

function HWD_InitCase(c)
    HWA_Freeze(c.source);HWA_Freeze(c.source2);HWA_Freeze(c.target);HWA_Freeze(c.guard)
    if c.guard~=c.target then SobGroup_SetInvulnerability(c.guard,1) end
    SobGroup_CreateIfNotExist(c.phase_group);SobGroup_Clear(c.phase_group)
    Selection_Create(c.old_selection)
    if c.defender~="" then
        if c.variant~="stock" and c.variant~="trace" then SobGroup_SetROE(c.defender,PassiveROE) end
        SobGroup_AbilityActivate(c.defender,AB_Attack,1)
        if c.variant~="stock" and c.variant~="trace" then SobGroup_SetSpeed(c.defender,0) end
    end
end

function HWD_Count(c,name,source)
    local point=c.x..",0,"..c.z
    return Selection_FilterInclude(name,source,"NearPoint",point,"18000")
end

function HWD_Tick(c)
    if c.index~=HWD_CURRENT then return end
    if not c.started_at then
        c.started_at=Universe_GameTime();c.initial_hp=HWA_Hp(c.target);c.peak=0;c.second_peak=0;c.last_sample=-1
        SobGroup_Clear("HWD_Active")
        if c.defender~="" then
            SobGroup_SobGroupAdd("HWD_Active",c.defender)
            SobGroup_GuardSobGroup(c.defender,c.guard)
        end
        HWD_Log(c,"baseline","variant="..c.variant.."|action="..c.action.."|hp="..c.initial_hp.."|expected_volley="..c.volley.."|source_owner="..c.source_player.."|defender_owner=5|allied="..AreAllied(5,c.source_player).."|command_attack="..COMMAND_Attack.."|command_guard="..COMMAND_Guard)
    end
    local t=Universe_GameTime()-c.started_at
    Selection_GetMissiles("HWD_AllMissiles")
    local count=HWD_Count(c,"HWD_Current", "HWD_AllMissiles")
    local old=0
    if c.first_snapshot then old=HWD_Count(c,"HWD_OldAlive",c.old_selection) end
    if t>=3 and not c.fired then
        c.fired=1;SobGroup_AbilityActivate(c.source,AB_Attack,1);SobGroup_Attack(c.source_player,c.source,c.target)
        HWD_Log(c,"fire_requested","phase=1|initial_missiles="..count)
    end
    if not c.second_fired and count>c.peak then c.peak=count end
    if count>0 and not c.first_launch then
        c.first_launch=Universe_GameTime()
        HWD_Log(c,"launch_observed","phase=1|count="..count)
    end
    if c.first_launch and not c.stopped and Universe_GameTime()-c.first_launch>=6 then
        c.stopped=1;SobGroup_Stop(c.source_player,c.source);SobGroup_AbilityActivate(c.source,AB_Attack,0)
    end
    if c.first_launch and not c.first_snapshot and count==c.volley then
        c.first_snapshot=1;c.first_snapshot_at=Universe_GameTime();HWD_Count(c,c.old_selection,"HWD_AllMissiles")
        HWD_Log(c,"snapshot","phase=1|count="..count.."|selection="..c.old_selection)
    end
    if c.action=="same_count" and c.first_snapshot_at and not c.first_paused and Universe_GameTime()-c.first_snapshot_at>=2 then
        c.first_paused=1;SobGroup_Stop(5,c.defender)
        HWD_Log(c,"observer_paused","phase=1|current_count="..count.."|result_order="..SobGroup_GetCurrentOrder(c.defender).."|count_cache_reset=0")
    end
    if c.action=="attack_order" and c.first_launch and not c.attack_ordered then
        c.attack_ordered=1
        local guarding=SobGroup_IsGuardingSobGroup(c.defender,c.guard)
        SobGroup_Stop(5,c.defender)
        SobGroup_AttackSelection(5,c.defender,"HWD_Current",c.attack_flag)
        HWD_Log(c,"explicit_missile_attack","flag="..c.attack_flag.."|prior_guarding="..guarding.."|result_order="..SobGroup_GetCurrentOrder(c.defender).."|selected_missiles="..count)
    end
    if c.first_launch and count==0 and not c.first_gone then
        c.first_gone=Universe_GameTime();c.old_gone_count=old
        HWD_Log(c,"cohort_gone","phase=1|old_alive="..old.."|count="..count)
    end
    if c.action=="same_count" and c.first_gone and not c.second_fired and Universe_GameTime()-c.first_gone>=4 then
        c.second_fired=1
        SobGroup_SobGroupAdd(c.phase_group,c.source2)
        -- Stop is a native player order; resume guard only once the full new cohort exists.
        -- This isolates equal-count replacement from the launcher's staggered 1 -> 2 birth.
        SobGroup_Stop(5,c.defender)
        SobGroup_AbilityActivate(c.source2,AB_Attack,1);SobGroup_Attack(c.source_player,c.source2,c.target)
        HWD_Log(c,"fire_requested","phase=2|old_alive="..old.."|prior_peak="..c.peak.."|observer_stopped=1|count_cache_reset=0")
    end
    if c.second_fired then
        if count>c.second_peak then c.second_peak=count end
        if count==c.volley and not c.second_guarded then
            c.second_guarded=1;SobGroup_GuardSobGroup(c.defender,c.guard)
            HWD_Log(c,"guard_reissued","phase=2|old_alive="..old.."|current_count="..count.."|count_cache_reset=0")
        end
        if count>0 and not c.second_launch then
            c.second_launch=Universe_GameTime();HWD_Log(c,"launch_observed","phase=2|count="..count.."|old_alive="..old)
        end
        if c.second_launch and not c.second_stopped and Universe_GameTime()-c.second_launch>=6 then
            c.second_stopped=1;SobGroup_Stop(c.source_player,c.source2);SobGroup_AbilityActivate(c.source2,AB_Attack,0)
        end
        if c.second_launch and count==0 and not c.second_gone then c.second_gone=Universe_GameTime() end
    end
    if c.last_sample<0 or t-c.last_sample>=1 then
        c.last_sample=t
        local guarding=-1;local order=-1;local ship_targets=-1
        if c.defender~="" then
            guarding=SobGroup_IsGuardingSobGroup(c.defender,c.guard);order=SobGroup_GetCurrentOrder(c.defender)
            SobGroup_CreateIfNotExist("HWD_CommandShips");SobGroup_Clear("HWD_CommandShips")
            SobGroup_GetCommandTargets("HWD_CommandShips",c.defender,COMMAND_Attack);ship_targets=SobGroup_Count("HWD_CommandShips")
        end
        HWD_Log(c,"sample","local_missiles="..count.."|old_alive="..old.."|target_hp="..HWA_Hp(c.target).."|guarding="..guarding.."|order="..order.."|ship_attack_targets="..ship_targets)
    end
    local finished=0
    if c.action=="same_count" then
        if c.second_gone and Universe_GameTime()-c.second_gone>=4 then finished=1 end
    elseif c.first_gone and Universe_GameTime()-c.first_gone>=4 then finished=1 end
    if finished==1 or t>=85 then
        local status="measured"
        if not c.first_snapshot or c.peak~=c.volley or (c.action=="same_count" and (not c.second_launch or c.second_peak~=c.volley or old~=0)) then status="blocked" end
        if Selection_GetMissiles("HWD_AllMissiles")~=0 then status="blocked" end
        local guarding=-1
        if c.defender~="" then guarding=SobGroup_IsGuardingSobGroup(c.defender,c.guard) end
        HWA_Result(c,status,"variant="..c.variant.."|action="..c.action.."|first_peak="..c.peak.."|second_peak="..c.second_peak.."|old_alive="..old.."|target_damage="..(c.initial_hp-HWA_Hp(c.target)).."|guarding="..guarding.."|elapsed="..t.."|ammo="..c.ammo)
        SobGroup_Stop(c.source_player,c.source2);SobGroup_AbilityActivate(c.source2,AB_Attack,0)
        SobGroup_Clear("HWD_Active");HWD_CURRENT=HWD_CURRENT+1
    end
end
