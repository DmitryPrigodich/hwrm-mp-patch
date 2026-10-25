-- Lua4 native-only autonomous cases. No mock, no manual result promotion.
dofilepath("data:scripts/SCAR/SCAR_Util.lua")
dofilepath("data:scripts/hwmp24/autotests/run.lua")

function HWA_Log(c,event,fields)
    print("HWMP_AUTO|v=1|run="..HWA_RUN.."|mode="..HWA_MODE.."|case="..(c.id or "suite")..
        "|t="..Universe_GameTime().."|event="..event.."|"..(fields or ""))
end

function HWA_Hp(g)
    if SobGroup_Count(g)==0 then return 0 end
    if SobGroup_CurrentHealthTotal then return SobGroup_CurrentHealthTotal(g) end
    return -1
end

function HWA_MaxHp(g)
    local h=HWA_Hp(g)
    if h<0 or SobGroup_Count(g)==0 then return -1 end
    local f=SobGroup_HealthPercentage(g)
    if f<=0 then return -1 end
    return h/f
end

function HWA_Distance(a,b)
    if SobGroup_Count(a)==0 or SobGroup_Count(b)==0 then return -1 end
    local p=SobGroup_GetPosition(a)
    local q=SobGroup_GetPosition(b)
    return sqrt((p[1]-q[1])^2+(p[2]-q[2])^2+(p[3]-q[3])^2)
end

function HWA_CountNear(c,point,radius)
    if not Selection_GetMissiles or not Selection_FilterInclude then return -1 end
    Selection_GetMissiles("HWA_AllMissiles")
    local p=point[1]..","..point[2]..","..point[3]
    return Selection_FilterInclude("HWA_NearMissiles","HWA_AllMissiles","NearPoint",p,""..radius)
end

function HWA_Result(c,status,fields)
    if c.done then return end
    c.done=1
    c.result=status
    HWA_Log(c,"result","status="..status.."|"..(fields or ""))
    if c.source and SobGroup_Count(c.source)>0 then
        SobGroup_Stop(c.source_player or 1,c.source)
        SobGroup_AbilityActivate(c.source,AB_Attack,0)
    end
end

function HWA_Freeze(g)
    SobGroup_SetROE(g,PassiveROE)
    SobGroup_AbilityActivate(g,AB_Attack,0)
    SobGroup_AbilityActivate(g,AB_Move,0)
    FOW_RevealGroup(g,1)
end

function HWA_InitCase(c)
    c.last_sample=-1
    if c.kind=="gravity" then
        SobGroup_SetROE(c.a,PassiveROE)
        SobGroup_SetROE(c.b,PassiveROE)
        SobGroup_SetROE(c.target,PassiveROE)
        SobGroup_SetROE(c.enemy,PassiveROE)
        SobGroup_AbilityActivate(c.target,AB_Attack,0)
        SobGroup_SetSpeed(c.target,0.75)
        c.base_speed=SobGroup_GetSpeed(c.target)
        c.base_move=SobGroup_CanDoAbility(c.target,AB_Move)
        c.base_attack=SobGroup_CanDoAbility(c.target,AB_Attack)
        c.base_enemy_move=SobGroup_CanDoAbility(c.enemy,AB_Move)
        HWA_Log(c,"baseline","move="..c.base_move.."|attack="..c.base_attack.."|enemy_move="..c.base_enemy_move.."|speed="..c.base_speed.."|configured_single_hw1_target=1")
    elseif c.kind=="missile" then
        HWA_Freeze(c.source);HWA_Freeze(c.target);HWA_Freeze(c.replacement)
        c.initial_hp=HWA_Hp(c.target);c.replacement_hp=HWA_Hp(c.replacement)
        c.peak_missiles=0
        HWA_Log(c,"baseline","hp="..c.initial_hp.."|replacement_hp="..c.replacement_hp.."|private_single_weapon=1|fire_interval=9999|expected_homogeneous_volley="..c.volley.."|armour="..c.armour.."|launcher="..c.launcher.."|action="..c.action)
    elseif c.kind=="death_control" then
        HWA_Freeze(c.target);HWA_Freeze(c.replacement);c.initial_hp=HWA_Hp(c.replacement)
    elseif c.kind=="platform_range" then
        HWA_Freeze(c.source);HWA_Freeze(c.target)
        c.initial_hp=HWA_Hp(c.target);c.peak_missiles=0
        HWA_Log(c,"baseline","distance="..HWA_Distance(c.source,c.target).."|source_move=0|target_move=0")
    elseif c.kind=="research_hp" then
        HWA_Freeze(c.target);c.before_max=HWA_MaxHp(c.target)
        HWA_Log(c,"baseline","hp_max="..c.before_max.."|tech="..c.tech.."|player="..c.player)
    elseif c.kind=="pass" then
        HWA_Freeze(c.source);HWA_Freeze(c.target)
        SobGroup_AbilityActivate(c.target,AB_Move,1)
        SobGroup_SetStance(c.source,NeutralStance)
        if c.stance==1 then SobGroup_SetStance(c.target,NeutralStance)
        else SobGroup_SetStance(c.target,EvasiveStance) end
        c.source_player=1
        if c.shooter=="flak" then c.source_player=0 end
        c.initial_hp=HWA_Hp(c.target);c.in_range=0;c.peak_speed=0
        HWA_Log(c,"baseline","hp="..c.initial_hp.."|shooter="..c.shooter.."|stance="..c.stance.."|native_stance="..SobGroup_GetStance(c.target).."|upgrade="..c.upgrade.."|target_owner="..c.owner)
    elseif c.kind=="economy" then
        HWA_Freeze(c.receiver)
        SobGroup_SetInvulnerability(c.receiver,1)
        SobGroup_AbilityActivate(c.receiver,AB_Builder,0)
        SobGroup_Create(c.id)
        for j=1,getn(c.members) do SobGroup_SobGroupAdd(c.id,c.members[j]) end
        c.initial_ru=Player_GetRU(c.player)
        HWA_Log(c,"baseline","ru="..c.initial_ru.."|collectors="..SobGroup_Count(c.id).."|count_configured="..c.count.."|initial_receiver_hp="..SobGroup_GetHardPointHealth(c.receiver,"Resource"))
    elseif c.kind=="progression" then
        HWA_Freeze(c.first);HWA_Freeze(c.second)
        Player_SetRU(c.player,10000)
        c.initial_ru=Player_GetRU(c.player)
        c.can_without_modules=Player_CanResearch(c.player,c.speed_tech)
        for j=1,getn(c.initial_modules) do SobGroup_CreateSubSystem(c.first,c.initial_modules[j]) end
        HWA_Log(c,"baseline","ru="..c.initial_ru.."|can_without_modules="..c.can_without_modules.."|modules_injected=1|producer_count=2")
    elseif c.kind=="dock" then
        HWA_Freeze(c.carrier)
        SobGroup_SetInvulnerability(c.carrier,1)
        SobGroup_AbilityActivate(c.carrier,AB_Builder,0)
        SobGroup_SetROE(c.target,PassiveROE)
        SobGroup_SetHealth(c.target,0.5)
        HWA_Log(c,"baseline","damage_fraction=0.5|physical_hull_loss=not_injected")
    end
end

function HWA_Gravity(c,t)
    if not SobGroup_CustomCommand then HWA_Result(c,"blocked","reason=CustomCommand_unavailable");return end
    if t>=4 and not c.a_on then
        c.a_on=1;SobGroup_CustomCommand(c.a);HWA_Log(c,"activate","generator=A")
    end
    if t>=7 and not c.first_check then
        c.first_check=1;c.first_move=SobGroup_CanDoAbility(c.target,AB_Move)
        HWA_Log(c,"first_field","move="..c.first_move.."|attack="..SobGroup_CanDoAbility(c.target,AB_Attack))
    end
    if t>=8 and not c.b_on then c.b_on=1;SobGroup_CustomCommand(c.b);HWA_Log(c,"activate","generator=B") end
    if t>=12 and not c.a_killed then c.a_killed=1;SobGroup_TakeDamage(c.a,1);HWA_Log(c,"destroy","generator=A") end
    if t>=15 and not c.remaining_check then
        c.remaining_check=1;c.remaining_move=SobGroup_CanDoAbility(c.target,AB_Move)
        c.remaining_enemy_move=SobGroup_CanDoAbility(c.enemy,AB_Move)
        HWA_Log(c,"remaining_field","move="..c.remaining_move.."|enemy_move="..c.remaining_enemy_move)
    end
    if t>=16 and not c.b_killed then c.b_killed=1;SobGroup_TakeDamage(c.b,1);HWA_Log(c,"destroy","generator=B") end
    if t>=20 then
        local move=SobGroup_CanDoAbility(c.target,AB_Move)
        local attack=SobGroup_CanDoAbility(c.target,AB_Attack)
        local enemy=SobGroup_CanDoAbility(c.enemy,AB_Move)
        local status="failed"
        if c.base_move==1 and c.first_move==0 and c.remaining_move==0 and c.remaining_enemy_move==0 and
           move==c.base_move and attack==c.base_attack and enemy==c.base_enemy_move and SobGroup_GetSpeed(c.target)==c.base_speed and
           SobGroup_Count(c.a)==0 and SobGroup_Count(c.b)==0 then status="passed" end
        HWA_Result(c,status,"move="..move.."|attack="..attack.."|enemy_move="..enemy.."|speed="..SobGroup_GetSpeed(c.target).."|release_mode=destruction|squadron_all_hulls_proven=0")
    end
end

function HWA_Missile(c,t)
    local count=HWA_CountNear(c,{c.x,0,c.z+1000},4500)
    if count<0 or c.initial_hp<0 then HWA_Result(c,"blocked","reason=required_native_measurement_API_unavailable");return end
    if count>c.peak_missiles then c.peak_missiles=count end
    if count>c.volley then c.contaminated=1 end
    if t>=4 and not c.started then
        if count~=0 then HWA_Result(c,"blocked","reason=missiles_present_before_fire");return end
        c.started=1
        SobGroup_AbilityActivate(c.source,AB_Attack,1)
        SobGroup_Attack(1,c.source,c.target)
        HWA_Log(c,"attack","initial_missiles=0")
    end
    if count>0 and not c.launched then
        c.launched=1;c.launch_time=t
        HWA_Log(c,"launch_observed","local_missiles="..count)
    end
    if c.action=="retarget" and c.launched and not c.killed and SobGroup_Count(c.target)>0 then
        local near=HWA_CountNear(c,SobGroup_GetPosition(c.target),550)
        if near>0 and count>0 and c.peak_missiles==c.volley then
            c.killed=1;c.kill_time=t;c.pre_kill_hp=HWA_Hp(c.replacement)
            SobGroup_Stop(1,c.source);SobGroup_AbilityActivate(c.source,AB_Attack,0)
            SobGroup_TakeDamage(c.target,1)
            HWA_Log(c,"target_loss","local_missiles="..count.."|near_primary="..near.."|replacement_hp="..c.pre_kill_hp.."|new_fire=disabled|cohort=single_homogeneous_volley")
        end
    end
    if c.last_sample<0 or t-c.last_sample>=1 then
        c.last_sample=t
        HWA_Log(c,"sample","local_missiles="..count.."|primary_hp="..HWA_Hp(c.target).."|replacement_hp="..HWA_Hp(c.replacement).."|primary_entries="..SobGroup_Count(c.target))
    end
    if (c.launched and count==0 and t-c.launch_time>=3) or t>=43 then
        local status="measured"
        if not c.launched then status="blocked" end
        if c.contaminated or c.peak_missiles~=c.volley then status="blocked" end
        if c.action=="retarget" and not c.killed then status="blocked" end
        HWA_Result(c,status,"launched="..(c.launched or 0).."|peak_missiles="..c.peak_missiles.."|expected_volley="..c.volley.."|cohort_contaminated="..(c.contaminated or 0).."|target_killed="..(c.killed or 0)..
            "|primary_damage="..(c.initial_hp-HWA_Hp(c.target)).."|replacement_damage="..(c.replacement_hp-HWA_Hp(c.replacement)).."|armour="..c.armour.."|launcher="..c.launcher.."|action="..c.action)
    end
end

function HWA_Pass(c,t)
    if t>=5 and not c.started then
        c.started=1;SobGroup_Move(c.owner,c.target,c.volume)
        SobGroup_AbilityActivate(c.source,AB_Attack,1)
        SobGroup_Attack(c.source_player,c.source,c.target)
        HWA_Log(c,"attack","source_move=0|target_attack=0")
    end
    if c.last_sample<0 or t-c.last_sample>=0.5 then
        local d=HWA_Distance(c.source,c.target)
        local speed=-1
        if SobGroup_Count(c.target)>0 and SobGroup_GetActualSpeed then speed=sqrt(SobGroup_GetActualSpeed(c.target)) end
        if speed>c.peak_speed then c.peak_speed=speed end
        local range=2500
        if c.shooter=="flak" then range=3000 end
        if d>=0 and d<=range and c.last_sample>=0 then c.in_range=c.in_range+t-c.last_sample end
        c.last_sample=t
        HWA_Log(c,"sample","hp="..HWA_Hp(c.target).."|entries="..SobGroup_Count(c.target).."|distance="..d.."|speed="..speed)
    end
    if t>=62 then
        local status="measured"
        if c.peak_speed<200 or c.in_range<1 or c.initial_hp<0 then status="blocked" end
        HWA_Result(c,status,"damage="..(c.initial_hp-HWA_Hp(c.target)).."|in_range_seconds="..c.in_range.."|peak_speed="..c.peak_speed.."|shooter="..c.shooter.."|stance="..c.stance.."|upgrade="..c.upgrade)
    end
end

function HWA_Economy(c,t)
    if t>=5 and not c.started then c.started=1;SobGroup_Resource(c.player,c.id);HWA_Log(c,"harvest_started","collectors="..SobGroup_Count(c.id)) end
    if t>=160 and not c.hit then
        c.hit=1
        SobGroup_SetHardPointHealth(c.receiver,"Resource",0)
        HWA_Log(c,"receiver_disabled_requested","hardpoint=Resource")
    end
    if c.last_sample<0 or t-c.last_sample>=1 then
        c.last_sample=t
        local hp=SobGroup_GetHardPointHealth(c.receiver,"Resource")
        if c.hit and hp<0.001 then c.disable_confirmed=1 end
        if c.disable_confirmed and not c.recovery_time and hp>0.001 then c.recovery_time=t;c.recovery_hp=hp end
        HWA_Log(c,"sample","ru="..Player_GetRU(c.player).."|collectors="..SobGroup_Count(c.id).."|receiver_hp="..hp)
    end
    if t>=350 then
        local income=Player_GetRU(c.player)-c.initial_ru
        local status="measured"
        if income<=0 then status="blocked" end
        HWA_Result(c,status,"income="..income.."|collectors="..SobGroup_Count(c.id).."|window=350|damage_time=160|disable_confirmed="..(c.disable_confirmed or 0).."|recovery_time="..(c.recovery_time or -1).."|recovery_hp="..(c.recovery_hp or -1))
    end
end

function HWA_Tick()
    local t=Universe_GameTime()-HWA_START
    local done=0
    for i=1,getn(HWA_CASES) do
        local c=HWA_CASES[i]
        if not c.done then
            if HWA_MODE=="SaveLoad" then HWA_SaveCase(c,t)
            elseif c.kind=="gravity" then HWA_Gravity(c,t)
            elseif c.kind=="missile" then HWA_Missile(c,t)
            elseif c.kind=="pass" then HWA_Pass(c,t)
            elseif c.kind=="economy" then HWA_Economy(c,t)
            elseif c.kind=="progression" then HWA_Progression(c,t)
            elseif c.kind=="platform_range" then
                local missiles=HWA_CountNear(c,{c.x,0,c.z+2500},8000)
                if missiles>c.peak_missiles then c.peak_missiles=missiles end
                if t>=4 and not c.started then
                    c.started=1;SobGroup_AbilityActivate(c.source,AB_Attack,1);SobGroup_Attack(1,c.source,c.target)
                end
                if t>=28 then
                    local status="failed"
                    local damage=c.initial_hp-HWA_Hp(c.target)
                    if c.distance==5800 and c.peak_missiles==0 and damage==0 then status="passed" end
                    if c.distance==5300 and c.peak_missiles>0 and damage>0 then status="passed" end
                    HWA_Result(c,status,"distance="..HWA_Distance(c.source,c.target).."|peak_missiles="..c.peak_missiles.."|damage="..damage.."|both_sides_individually_identified=0")
                end
            elseif c.kind=="dock" then
                if t>=4 and not c.started then c.started=1;SobGroup_DockSobGroupAndStayDocked(c.target,c.carrier);HWA_Log(c,"dock_order","") end
                if t>=8 and SobGroup_IsDocked(c.target)==1 then HWA_Result(c,"passed","native_docked=1|forced_stall=0|under_fire=0|hull_count_proven=0")
                elseif t>=45 then HWA_Result(c,"failed","native_docked=0|forced_stall=0|under_fire=0") end
            elseif c.kind=="death_control" then
                if t>=10 and not c.killed then c.killed=1;SobGroup_TakeDamage(c.target,1) end
                if t>=25 then HWA_Result(c,"measured","blast_damage="..(c.initial_hp-HWA_Hp(c.replacement))) end
            elseif c.kind=="research_hp" then
                if t>=4 and not c.granted then
                    c.granted=1;if Player_HasResearch(c.player,c.tech)==0 then Player_GrantResearchOption(c.player,c.tech) end
                    HWA_Log(c,"grant_requested","tech="..c.tech)
                end
                if t>=12 then
                    local after=HWA_MaxHp(c.target)
                    local ratio=-1
                    if c.before_max>0 then ratio=after/c.before_max end
                    local status="failed"
                    if abs(ratio-c.expected)<0.01 and Player_HasResearch(c.player,c.tech)==1 then status="passed" end
                    if ratio<0 then status="blocked" end
                    HWA_Result(c,status,"before="..c.before_max.."|after="..after.."|ratio="..ratio.."|expected="..c.expected.."|research_flag="..Player_HasResearch(c.player,c.tech))
                end
            end
        end
        if c.done then done=done+1 end
    end
    if t-HWA_LAST_PROGRESS>=10 then HWA_LAST_PROGRESS=t;HWA_Log({id="suite"},"progress","finished="..done.."|total="..getn(HWA_CASES)) end
    if done==getn(HWA_CASES) then
        HWA_Log({id="suite"},"end","finished="..done.."|total="..getn(HWA_CASES))
        Subtitle_Message("Automatic run complete. Results are in HwRM.log.",30)
        Rule_Remove("HWA_Tick")
    end
end

function HWA_Progression(c,t)
    if t>=4 and not c.initial_check then
        c.initial_check=1;c.can_initial=Player_CanResearch(c.player,c.speed_tech)
        HWA_Log(c,"initial_gate","can_research="..c.can_initial.."|initial_modules="..getn(c.initial_modules))
    end
    if t>=8 and not c.completed_modules then
        c.completed_modules=1
        local has_research=0
        local has_fighter=0
        for j=1,getn(c.initial_modules) do
            if c.initial_modules[j]=="Research" then has_research=1 end
            if c.initial_modules[j]=="FighterProduction" then has_fighter=1 end
        end
        if has_research==0 and c.player~=2 then SobGroup_CreateSubSystem(c.first,"Research") end
        if has_fighter==0 then SobGroup_CreateSubSystem(c.first,"FighterProduction") end
        if c.lab_count==2 then SobGroup_CreateSubSystem(c.second,"Research") end
        SobGroup_CreateSubSystem(c.second,"FighterProduction")
        HWA_Log(c,"modules_completed","laboratories_requested="..c.lab_count)
    end
    if t>=12 and not c.requested then
        c.requested=1;c.request_time=t
        c.can_complete=Player_CanResearch(c.player,c.speed_tech)
        if c.can_complete==1 and Player_CanResearch(c.player,c.second_tech)==1 then
            Player_Research(c.player,c.speed_tech)
            HWA_Log(c,"research_requested","can_research="..c.can_complete.."|first="..c.speed_tech.."|second="..c.second_tech)
        else HWA_Result(c,"blocked","reason=completed_modules_did_not_unlock_research");return end
    end
    if c.requested then
        if t>=13 and not c.second_requested then
            c.second_requested=1;c.first_queued_at_enqueue=Player_HasQueuedResearch(c.player,c.speed_tech)
            c.first_spending_at_enqueue=c.initial_ru-Player_GetRU(c.player)
            Player_Research(c.player,c.second_tech)
            HWA_Log(c,"second_requested","first_queued="..c.first_queued_at_enqueue.."|first_spending="..c.first_spending_at_enqueue)
        end
        if not c.first_done and Player_HasResearch(c.player,c.speed_tech)==1 then c.first_done=t-c.request_time;HWA_Log(c,"first_completed","elapsed="..c.first_done) end
        if not c.second_done and Player_HasResearch(c.player,c.second_tech)==1 then c.second_done=t-c.request_time;HWA_Log(c,"second_completed","elapsed="..c.second_done) end
        if c.last_sample<0 or t-c.last_sample>=1 then
            c.last_sample=t
            local a=Player_HasQueuedResearch(c.player,c.speed_tech)
            local b=Player_HasQueuedResearch(c.player,c.second_tech)
            if a==1 and b==1 then c.both_queued=1 end
            HWA_Log(c,"sample","ru="..Player_GetRU(c.player).."|first_queued="..a.."|second_queued="..b)
        end
        if (c.first_done and c.second_done) or t>=115 then
            local status="failed"
            local spent=c.initial_ru-Player_GetRU(c.player)
            if c.first_done and c.second_done and c.first_done<c.second_done and c.first_queued_at_enqueue==1 and c.first_spending_at_enqueue>0 and abs(c.second_done-c.first_done*(c.speed_time+c.second_time)/c.speed_time)<1 and c.can_without_modules==0 and c.can_initial==c.initial_can_expected and spent==c.speed_cost+c.second_cost then status="passed" end
            local helper="InstaAdvancedFrigateTech"
            if c.race=="vgr" then helper="ScoutSpeedLimiter" end
            HWA_Result(c,status,"can_without_modules="..c.can_without_modules.."|can_initial="..c.can_initial.."|can_complete="..c.can_complete.."|first_elapsed="..(c.first_done or -1).."|second_elapsed="..(c.second_done or -1).."|spent="..spent.."|expected_cost="..(c.speed_cost+c.second_cost).."|laboratories_requested="..c.lab_count.."|both_queued="..(c.both_queued or 0).."|automatic_helper_flag="..Player_HasResearch(c.player,helper))
        end
    end
end

function OnInit()
    HWA_START=Universe_GameTime();HWA_LAST_PROGRESS=-10
    HWA_Log({id="suite"},"begin","total="..getn(HWA_CASES).."|native=1|physical_hull_counts_inferred=0")
    HWA_Log({id="suite"},"native_constants","neutral="..NeutralStance.."|evasive="..EvasiveStance.."|aggressive="..AggressiveStance)
    for p=1,5 do CPU_Enable(p,0) end
    if Selection_Create then Selection_Create("HWA_AllMissiles");Selection_Create("HWA_NearMissiles") end
    HWA_Freeze("HWA_MotherH");HWA_Freeze("HWA_MotherV")
    SobGroup_SetInvulnerability("HWA_MotherH",1);SobGroup_SetInvulnerability("HWA_MotherV",1)
    SobGroup_AbilityActivate("HWA_MotherH",AB_Builder,0);SobGroup_AbilityActivate("HWA_MotherV",AB_Builder,0)
    if HWA_MODE=="Antistrike" then
        Player_GrantResearchOption(2,"InterceptorMAXSPEEDUpgrade1")
        Player_GrantResearchOption(3,"FighterspeedUpgrade1")
        HWA_Log({id="suite"},"speed_grants","hgn="..Player_HasResearch(2,"InterceptorMAXSPEEDUpgrade1").."|vgr="..Player_HasResearch(3,"FighterspeedUpgrade1"))
    end
    for i=1,getn(HWA_CASES) do HWA_InitCase(HWA_CASES[i]) end
    Camera_Interpolate("here","HWA_Home",0)
    if HWA_MODE=="Mechanics" or HWA_MODE=="Antistrike" or HWA_MODE=="SaveLoad" then Camera_Interpolate("here",HWA_CASES[1].id,0) end
    Subtitle_Message("$9985001",20)
    Rule_AddInterval("HWA_Tick",0.25)
end

function OnStartOrLoad()
    HWA_LOADS=(HWA_LOADS or 0)+1
    HWA_Log({id="suite"},"start_or_load","load_count="..HWA_LOADS)
    if HWA_MODE=="SaveLoad" and HWA_SAVE_REQUESTED==1 and HWA_LOADS>=2 then
        HWA_RELEASE_START=Universe_GameTime()
        HWA_Log({id="suite"},"save_loaded","saved_globals_restored=1")
        HWA_EffectState("after_load")
    end
end

function HWA_SaveCase(c,t)
    if t>=1 and not c.a_on then c.a_on=1;SobGroup_CustomCommand(c.a) end
    if t>=2.5 and not c.b_on then c.b_on=1;SobGroup_CustomCommand(c.b) end
    if HWA_RELEASE_START then
        local dt=Universe_GameTime()-HWA_RELEASE_START
        if dt>=2 and not c.a_killed then c.a_killed=1;SobGroup_TakeDamage(c.a,1) end
        if dt>=5 and not c.check then c.check=1;c.remaining=SobGroup_CanDoAbility(c.target,AB_Move) end
        if dt>=6 and not c.b_killed then c.b_killed=1;SobGroup_TakeDamage(c.b,1) end
        if dt>=10 then
            local status="failed"
            local alive=SobGroup_Count(c.a)+SobGroup_Count(c.b)
            if c.remaining==0 and SobGroup_CanDoAbility(c.target,AB_Move)==c.base_move and
               SobGroup_CanDoAbility(c.target,AB_Attack)==c.base_attack and SobGroup_GetSpeed(c.target)==c.base_speed and alive==0 then status="passed" end
            if alive>0 then status="blocked" end
            HWA_Result(c,status,"after_real_load=1|remaining_field_move="..c.remaining.."|final_move="..SobGroup_CanDoAbility(c.target,AB_Move).."|final_attack="..SobGroup_CanDoAbility(c.target,AB_Attack).."|speed="..SobGroup_GetSpeed(c.target).."|generators_remaining="..alive.."|generator_a_hp="..HWA_Hp(c.a).."|generator_b_hp="..HWA_Hp(c.b))
            HWA_EffectState("after_destroy")
        end
    elseif t>=5 and not HWA_SAVE_REQUESTED then
        HWA_SAVE_REQUESTED=1
        HWA_Log({id="suite"},"save_requested","field_active="..(1-SobGroup_CanDoAbility(c.target,AB_Move)).."|checkpoint=HWMP_AutoFields_"..strsub(HWA_RUN,1,8).."|universe_pause=0")
        HWA_EffectState("before_save")
        Campaign_QuickSaveNb(5,"HWMP_AutoFields_"..strsub(HWA_RUN,1,8))
    end
end

function HWA_EffectState(phase)
    local count=-1
    if type(HWMP_EffectRecords)=="table" then
        count=getn(HWMP_EffectRecords)
        for i=1,count do
            local record=HWMP_EffectRecords[i]
            local baseline=-1
            if record.speed then baseline=record.speed.baseline end
            HWA_Log({id="effect_"..i},"effect_record","phase="..phase.."|group="..record.group.."|speed_baseline="..baseline)
        end
    end
    HWA_Log({id="suite"},"effect_state","phase="..phase.."|records="..count)
end
