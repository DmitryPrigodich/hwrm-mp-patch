function HWB_Init(c)
    HWA_Freeze(c.mother);HWA_Freeze(c.old)
    SobGroup_CreateSubSystem(c.mother,c.race=="hgn" and "AdvancedResearch" or "Research")
    SobGroup_CreateSubSystem(c.mother,"CapShipProduction")
    SobGroup_CreateSubSystem(c.old,"FighterProduction")
    SobGroup_AbilityActivate(c.mother,AB_Builder,0)
    SobGroup_CreateIfNotExist(c.fresh)
    Player_SetRU(c.player,10000);c.initial_ru=Player_GetRU(c.player)
    if CPU_Exist and CPU_Exist(c.player)==1 and CPU_DoString then
        CPU_DoString(c.player,"sg_dobuild=0;sg_dosubsystems=0;sg_doresearch=0;sg_doupgrades=0;sg_domilitary=0;cp_processResource=0;cp_processMilitary=0")
        CPU_Enable(c.player,1)
    end
    c.phase=0;c.next=12;c.records={};c.last_sample=-1
    local ai=-1;if CPU_Exist then ai=CPU_Exist(c.player) end
    HWA_Log(c,"production_baseline","item="..c.item.."|item_cost="..c.item_cost.."|base_time="..c.item_base_time.."|research_paid="..c.upgrade.."|CPU_exists="..ai.."|can_research="..Player_CanResearch(c.player,c.tech).."|modules_injected=1|one_eligible_fighter_builder=1|autonomous_AI_features_disabled=1")
end

function HWB_Request(c,t)
    c.producer=c.phase==2 and c.fresh or c.old
    c.before_count=Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(c.player,c.item)
    c.before_ru=Player_GetRU(c.player);c.requested=t;c.build_start=nil
    local code='if type('..c.item_id..')=="number" and type(Build)=="function" and type(CanBuild)=="function" then print("HWMP_PRODUCTION_AI|item='..c.item..'|can="..CanBuild('..c.item_id..')); if CanBuild('..c.item_id..')==1 then Build('..c.item_id..') end else print("HWMP_PRODUCTION_AI|unsupported_context=1") end'
    CPU_DoString(c.player,code)
    HWA_Log(c,"production_requested","phase="..c.phase.."|producer="..c.producer.."|ru="..c.before_ru.."|count_before="..c.before_count.."|backend=CPU_DoString_Build")
end

function HWB_Tick(c,t)
    if not CPU_DoString or not CPU_Exist or CPU_Exist(c.player)~=1 then HWA_Result(c,"blocked","reason=native_AI_context_unavailable");return end
    if c.phase==1 and c.await_research then
        if Player_HasResearch(c.player,c.tech)==1 then
            c.await_research=nil;c.next=t+4
            c.research_spent=c.research_ru-Player_GetRU(c.player)
            HWA_Log(c,"production_research_done","elapsed="..(t-c.research_at).."|spent="..c.research_spent.."|expected_spent="..c.research_cost)
        elseif t-c.research_at>120 then HWA_Result(c,"blocked","reason=paid_buildspeed_research_not_completed");return end
    end
    if c.phase==2 and not c.fresh_created then
        c.fresh_created=t
        SobGroup_SpawnNewShipInSobGroup(c.player,c.carrier_type,c.fresh,c.fresh,c.volume)
        SobGroup_AbilityActivate(c.old,AB_Builder,0);SobGroup_RestrictBuildOption(c.old,c.item)
        c.next=t+5
    end
    if c.phase==2 and c.fresh_created and t-c.fresh_created>=2 and not c.fresh_factory then
        c.fresh_factory=1;HWA_Freeze(c.fresh);SobGroup_CreateSubSystem(c.fresh,"FighterProduction")
        HWA_Log(c,"production_new_carrier","spawned_after_research=1|producer_creation_not_paid=1")
    end
    if c.next and t>=c.next and not c.requested and not c.await_research then c.next=nil;HWB_Request(c,t) end
    if c.requested then
        local building=SobGroup_IsBuilding(c.producer,c.item)
        local queued=Player_HasQueuedBuild(c.player,c.item)
        local count=Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(c.player,c.item)
        local spent=c.before_ru-Player_GetRU(c.player)
        if building==1 and not c.build_start then c.build_start=t;HWA_Log(c,"production_started","phase="..c.phase.."|producer="..c.producer) end
        if c.last_sample<0 or t-c.last_sample>=0.5 then
            c.last_sample=t;HWA_Log(c,"production_sample","phase="..c.phase.."|building="..building.."|queued="..queued.."|count="..count.."|spent="..spent)
        end
        if c.build_start and building==0 and queued==0 and count>c.before_count then
            local elapsed=t-c.build_start
            c.records[c.phase+1]={elapsed=elapsed,spent=spent}
            HWA_Log(c,"production_phase_result","phase="..c.phase.."|elapsed="..elapsed.."|spent="..spent.."|count_delta="..(count-c.before_count).."|producer="..c.producer)
            c.requested=nil;c.phase=c.phase+1;c.next=t+4
            if c.phase==1 and c.upgrade==1 then
                c.await_research=1;c.research_at=t;c.research_ru=Player_GetRU(c.player)
                Player_Research(c.player,c.tech)
            elseif c.phase==3 then
                local status="passed";local expected=c.upgrade==1 and 1.3 or 1
                for j=1,3 do if c.records[j].spent~=c.item_cost then status="failed" end end
                if c.upgrade==1 and c.research_spent~=c.research_cost then status="failed" end
                if abs(c.records[1].elapsed/c.records[2].elapsed-expected)>0.08 or abs(c.records[1].elapsed/c.records[3].elapsed-expected)>0.08 then status="failed" end
                HWA_Result(c,status,"old_before="..c.records[1].elapsed.."|old_after="..c.records[2].elapsed.."|new_after="..c.records[3].elapsed.."|expected_speed_ratio="..expected.."|total_spent="..(c.initial_ru-Player_GetRU(c.player)).."|native_paid_builds=3|new_producer_spawned_not_paid=1|AI_backend_not_UI=1")
            end
        elseif t-c.requested>100 then HWA_Result(c,"blocked","reason=paid_native_build_not_completed|building="..building.."|queued="..queued.."|spent="..spent.."|count="..count);return end
    end
    if t>=400 then HWA_Result(c,"blocked","reason=production_suite_timeout") end
end
