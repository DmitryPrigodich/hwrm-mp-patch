function HWE_Init(c)
    c.base_hp={};c.base_peak={0,0};c.old_peak={0,0};c.new_peak={0,0};c.last_sample=-1
    HWA_Freeze(c.mother)
    for j=1,getn(c.members) do
        SobGroup_SetROE(c.members[j],PassiveROE);SobGroup_SetStance(c.members[j],NeutralStance)
        SobGroup_AbilityActivate(c.members[j],AB_Attack,0)
        if j>=3 then c.base_hp[j]=HWA_MaxHp(c.members[j]);SobGroup_AbilityActivate(c.members[j],AB_Move,0) end
        SobGroup_CreateIfNotExist(c.fresh[j])
    end
    HWA_Log(c,"effects_baseline","granted_not_paid=1|upgraded="..c.upgraded.."|hp1="..c.base_hp[3].."|hp2="..c.base_hp[4].."|old_and_new_actual_stock_types=1")
end

function HWE_Tick(c,t)
    if t>=3 and not c.started then
        c.started=1
        for j=1,2 do SobGroup_Move(c.player,c.members[j],c.routes[j]) end
    end
    if t>=25 and not c.granted then
        c.granted=1
        for j=1,2 do SobGroup_Stop(c.player,c.members[j]) end
        if c.upgraded==1 then
            Player_GrantResearchOption(c.player,c.speed_tech);Player_GrantResearchOption(c.player,c.hp_tech)
        end
        HWA_Log(c,"effects_grant","speed="..Player_HasResearch(c.player,c.speed_tech).."|health="..Player_HasResearch(c.player,c.hp_tech).."|explicit_grant=1|payment_tested_separately=1")
    end
    if t>=33 and not c.spawned then
        c.spawned=1
        for j=1,getn(c.members) do
            SobGroup_SpawnNewShipInSobGroup(c.player,c.types[j],c.fresh[j],c.fresh[j],c.starts[j])
            SobGroup_SetROE(c.fresh[j],PassiveROE);SobGroup_SetStance(c.fresh[j],NeutralStance)
            SobGroup_AbilityActivate(c.fresh[j],AB_Attack,0)
            if j>=3 then SobGroup_AbilityActivate(c.fresh[j],AB_Move,0) end
        end
        HWA_Log(c,"effects_fresh_spawned","spawn_not_paid_production=1")
    end
    if t>=36 and not c.after_started then
        c.after_started=1
        for j=1,2 do SobGroup_Move(c.player,c.members[j],c.routes[j]);SobGroup_Move(c.player,c.fresh[j],c.routes[j]) end
    end
    if c.last_sample<0 or t-c.last_sample>=0.5 then
        c.last_sample=t
        for j=1,2 do
            local old_speed=sqrt(SobGroup_GetActualSpeed(c.members[j]))
            local new_speed=-1
            if c.spawned then new_speed=sqrt(SobGroup_GetActualSpeed(c.fresh[j])) end
            if t>=10 and t<25 then c.base_peak[j]=max(c.base_peak[j],old_speed) end
            if t>=44 then c.old_peak[j]=max(c.old_peak[j],old_speed);c.new_peak[j]=max(c.new_peak[j],new_speed) end
            HWA_Log(c,"effects_speed","member="..j.."|old_speed="..old_speed.."|new_speed="..new_speed)
        end
    end
    if t>=72 then
        local passed=1
        for j=1,2 do
            local expected=1
            if c.upgraded==1 and j==1 then expected=1.4 end
            local old_ratio=c.old_peak[j]/max(c.base_peak[j],1)
            local new_ratio=c.new_peak[j]/max(c.base_peak[j],1)
            if c.base_peak[j]<100 or abs(old_ratio-expected)>0.06 or abs(new_ratio-expected)>0.06 then passed=0 end
            HWA_Log(c,"effects_speed_result","member="..j.."|baseline_peak="..c.base_peak[j].."|old_peak="..c.old_peak[j].."|new_peak="..c.new_peak[j].."|expected_ratio="..expected.."|old_ratio="..old_ratio.."|new_ratio="..new_ratio)
        end
        for j=3,4 do
            local expected=1
            if c.upgraded==1 and (j==3 or c.race=="vgr") then expected=1.4 end
            local old=HWA_MaxHp(c.members[j]);local fresh=HWA_MaxHp(c.fresh[j])
            if abs(old/c.base_hp[j]-expected)>0.005 or abs(fresh/c.base_hp[j]-expected)>0.005 then passed=0 end
            HWA_Log(c,"effects_hp_result","member="..j.."|baseline="..c.base_hp[j].."|old="..old.."|fresh="..fresh.."|expected_ratio="..expected)
        end
        local helper=-1
        if c.race=="vgr" then helper=Player_HasResearch(c.player,"ScoutSpeedLimiter") end
        local status="failed"
        if passed==1 then status="passed" end
        HWA_Result(c,status,"upgraded="..c.upgraded.."|speed_flag="..Player_HasResearch(c.player,c.speed_tech).."|health_flag="..Player_HasResearch(c.player,c.hp_tech).."|scout_limiter="..helper.."|granted_not_paid=1|new_hulls_spawned_not_built=1|save_load_not_tested=1")
    end
end
