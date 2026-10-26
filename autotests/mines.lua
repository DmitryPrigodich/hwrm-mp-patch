function HWM_Init(c)
    HWA_Freeze(c.source);SobGroup_SetInvulnerability(c.source,1)
    HWA_Freeze(c.sensor);SobGroup_SetInvulnerability(c.sensor,1)
    SobGroup_SetROE(c.deployer,PassiveROE);SobGroup_AbilityActivate(c.deployer,AB_Attack,0)
    BreakAlliance(0,1);BreakAlliance(1,0)
    Selection_Create(c.selection);Selection_Create(c.snapshot);Selection_Create(c.alive)
    c.last_sample=-1;c.peak=0
    HWA_Log(c,"mine_baseline","source="..c.shooter_kind.."|fire="..c.fire.."|private_mine_detection=0|private_mine_speed=1|stock_HP_armour_family_lifetime=1")
end

function HWM_Tick(c,t)
    if not SobGroup_DeployMines or not SobGroup_AttackSelection then HWA_Result(c,"blocked","reason=native_mine_API_unavailable");return end
    Selection_GetMissiles("HWA_AllMissiles")
    Selection_FilterInclude(c.selection,"HWA_AllMissiles","NearPoint",c.x..",0,"..(c.z+1000),"3000")
    local count=Selection_FilterInclude(c.selection,c.selection,"PlayerOwner","1","")
    if t>=3 and not c.requested then
        c.requested=1;SobGroup_DeployMines(c.deployer,c.volume,0.1)
        HWA_Log(c,"native_mines_requested","density=0.1")
    end
    if count>c.peak then c.peak=count end
    if count>0 and not c.stopped then
        c.stopped=t;SobGroup_Stop(1,c.deployer)
        HWA_Log(c,"mine_cohort_observed","count="..count)
    end
    if c.stopped and not c.attack_at then
        if count~=c.previous_count then c.quiet_since=t end
        c.previous_count=count
        if c.quiet_since and t-c.quiet_since>=4 and count>0 then
            c.attack_at=t;c.initial=count
            Selection_FilterInclude(c.snapshot,c.selection,"PlayerOwner","1","")
            if c.fire==1 then SobGroup_AbilityActivate(c.source,AB_Attack,1);SobGroup_AttackSelection(0,c.source,c.snapshot,0) end
            HWA_Log(c,"mine_attack_started","initial="..count.."|fire="..c.fire.."|explicit_selection_flag=0")
        end
    end
    local remaining=Selection_FilterInclude(c.alive,c.snapshot,"PlayerOwner","1","")
    if c.attack_at and count>remaining then c.contaminated=1 end
    if c.last_sample<0 or t-c.last_sample>=0.5 then
        c.last_sample=t
        HWA_Log(c,"mine_sample","local_count="..count.."|snapshot_alive="..remaining.."|order="..SobGroup_GetCurrentOrder(c.source))
    end
    if c.attack_at and t-c.attack_at>=25 or t>=85 then
        local status="measured"
        if not c.attack_at or c.contaminated then status="blocked" end
        HWA_Result(c,status,"source="..c.shooter_kind.."|fire="..c.fire.."|initial="..(c.initial or 0).."|remaining="..remaining.."|local_count="..count.."|cohort_contaminated="..(c.contaminated or 0).."|stationary_diagnostic_mines_not_combat_effectiveness=1")
    end
end
