function HWV_Init(c)
    HWA_Freeze(c.receiver);SobGroup_SetInvulnerability(c.receiver,c.method=="real_shots" and 0 or 1)
    SobGroup_CreateIfNotExist(c.id)
    for j=1,getn(c.members) do
        SobGroup_SobGroupAdd(c.id,c.members[j]);SobGroup_SetInvulnerability(c.members[j],1)
        SobGroup_SetROE(c.members[j],PassiveROE)
    end
    if c.source~="" then
        HWA_Freeze(c.source);SobGroup_Despawn(c.source)
        BreakAlliance(c.player,c.enemy);BreakAlliance(c.enemy,c.player)
    end
    c.initial_ru=Player_GetRU(c.player);c.last_sample=-1;c.previous_ru=c.initial_ru
    c.docked=c.id.."_docked";SobGroup_CreateIfNotExist(c.docked)
    HWA_Log(c,"recovery_baseline","method="..c.method.."|collectors_invulnerable=1|actual_resource_health="..SobGroup_GetHardPointHealth(c.receiver,"Resource"))
end

function HWV_Tick(c,t)
    if t>=5 and not c.started then c.started=1;SobGroup_Resource(c.player,c.id) end
    if t>=90 and not c.attack_started then
        c.attack_started=t
        if c.method=="real_shots" then SobGroup_Spawn(c.source,c.spawn)
        else SobGroup_SetHardPointHealth(c.receiver,"Resource",0) end
        HWA_Log(c,"recovery_hit_requested","method="..c.method.."|ru="..Player_GetRU(c.player))
    end
    if c.method=="real_shots" and c.attack_started and t-c.attack_started>=1 and not c.attack_sent then
        c.attack_sent=1;SobGroup_AbilityActivate(c.source,AB_Attack,1)
        SobGroup_AttackSobGroupHardPoint(c.source,c.receiver,"Resource")
        HWA_Log(c,"native_subsystem_attack","hardpoint=Resource|source_real="..SobGroup_AreAllInRealSpace(c.source))
    end
    local hp=SobGroup_GetHardPointHealth(c.receiver,"Resource")
    if c.attack_started and hp<0.001 and not c.disabled then
        c.disabled=t;c.ru_disabled=Player_GetRU(c.player)
        if c.source~="" then SobGroup_Stop(c.enemy,c.source);SobGroup_AbilityActivate(c.source,AB_Attack,0);SobGroup_Despawn(c.source) end
        HWA_Log(c,"recovery_disabled","ru="..c.ru_disabled.."|receiver_hull_hp="..HWA_Hp(c.receiver))
    end
    if c.disabled and hp>=0.05 and not c.woke then
        c.woke=t;c.ru_woke=Player_GetRU(c.player)
        HWA_Log(c,"recovery_woke","since_damage="..(t-c.disabled).."|ru="..c.ru_woke.."|resource_hp="..hp)
    end
    if c.woke and c.method=="api_reissue" then
        if t-c.woke>=5 and not c.reissued then
            c.reissued=t;c.ru_reissued=Player_GetRU(c.player)
            SobGroup_Stop(c.player,c.id);SobGroup_Resource(c.player,c.id)
            HWA_Log(c,"recovery_resource_reissued","ru="..c.ru_reissued.."|only_fixture_order=1")
        elseif c.reissued and t-c.reissued>=45 and Player_GetRU(c.player)==c.ru_reissued and not c.forced_launch then
            c.forced_launch=t;SobGroup_Launch(c.id,c.receiver);SobGroup_Resource(c.player,c.id)
            HWA_Log(c,"recovery_launch_then_resource","ru="..Player_GetRU(c.player).."|after_failed_reissue=1")
        end
    end
    if c.last_sample<0 or t-c.last_sample>=1 then
        c.last_sample=t
        local ru=Player_GetRU(c.player)
        SobGroup_Clear(c.docked);SobGroup_GetSobGroupDockedWithGroup(c.receiver,c.docked)
        HWA_Log(c,"recovery_sample","ru="..ru.."|resource_hp="..hp.."|dock_group_count="..SobGroup_Count(c.docked).."|receiver_alive="..SobGroup_Count(c.receiver))
        for j=1,getn(c.members) do
            local g=c.members[j]
            HWA_Log(c,"collector_recovery_state","member="..j.."|order="..SobGroup_GetCurrentOrder(g).."|actual_speed="..SobGroup_GetActualSpeed(g).."|docked="..SobGroup_IsDocked(g).."|real="..SobGroup_AreAllInRealSpace(g).."|distance="..HWA_Distance(g,c.receiver).."|can_harvest="..SobGroup_CanDoAbility(g,AB_Harvest).."|can_dock="..SobGroup_CanDoAbility(g,AB_Dock))
        end
        if c.woke and ru>c.previous_ru and not c.credit_after_wake then c.credit_after_wake=t;HWA_Log(c,"recovery_credit_after_wake","since_wake="..(t-c.woke).."|ru="..ru) end
        c.previous_ru=ru
    end
    if t>=360 then
        local status="measured";if not c.woke then status="blocked" end
        HWA_Result(c,status,"method="..c.method.."|disabled_at="..(c.disabled or -1).."|woke_at="..(c.woke or -1).."|first_credit_after_wake="..(c.credit_after_wake or -1).."|income="..(Player_GetRU(c.player)-c.initial_ru).."|since_wake_income="..(Player_GetRU(c.player)-(c.ru_woke or Player_GetRU(c.player))).."|reissued="..(c.reissued or -1).."|forced_launch="..(c.forced_launch or -1).."|collectors="..SobGroup_Count(c.id))
    end
end
