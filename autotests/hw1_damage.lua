HWQ_Players={}
function HWQ_Init(c)
    if not HWQ_Players[c.owner] then
        Player_SetRU(c.owner,10000)
        HWQ_Players[c.owner]={phase=0,start=8,finish=68,initial_ru=Player_GetRU(c.owner),stage="fire"}
    end
    BreakAlliance(c.source_player,c.enemy);BreakAlliance(c.enemy,c.source_player)
    SobGroup_CreateIfNotExist(c.source);HWA_Freeze(c.target)
    if c.variant~="new" then HWA_Freeze(c.source);SobGroup_SetStance(c.source,NeutralStance) end
    c.phase=-1;c.metrics={};c.last_sample=-1
    HWA_Log(c,"damage_baseline","constant_private_weapon=100|one_gun=1|spatial_falloff_removed=1|source_owner="..c.source_player.."|research_owner="..c.owner.."|variant="..c.variant)
end

function HWQ_Tick(c,t)
    local s=HWQ_Players[c.owner]
    if c.driver==1 then
        if s.stage=="fire" and t>=s.finish+5 then
            if s.phase==2 then s.stage="done"
            else
                local tech="FighterDamageLevel"..(s.phase+1)
                local can=Player_CanResearch(c.owner,tech)
                HWA_Log(c,"damage_research_requested","tech="..tech.."|can="..can.."|ru="..Player_GetRU(c.owner))
                if can==1 then Player_Research(c.owner,tech);s.requested=t;s.tech=tech;s.stage="research" else s.stage="blocked" end
            end
        elseif s.stage=="research" and Player_HasResearch(c.owner,s.tech)==1 then
            s.phase=s.phase+1;s.stage="fire";s.start=t+8;s.finish=t+68
            HWA_Log(c,"damage_research_completed","tech="..s.tech.."|elapsed="..(t-s.requested).."|phase="..s.phase.."|spent="..(s.initial_ru-Player_GetRU(c.owner)))
        end
    end
    if c.phase~=s.phase then
        c.phase=s.phase;c.firing=nil;c.phase_result=nil;c.previous_hp=nil
        c.min_hit=nil;c.hits=0;c.damage=0;c.start_hp=HWA_Hp(c.target)
        SobGroup_SetHealth(c.target,1);c.start_hp=HWA_Hp(c.target)
        if c.variant=="new" and s.phase>0 then
            c.source=c.id.."_phase"..s.phase;SobGroup_CreateIfNotExist(c.source)
            SobGroup_SpawnNewShipInSobGroup(c.source_player,c.source_type,c.source,c.source,c.volume)
            HWA_Freeze(c.source);SobGroup_SetStance(c.source,NeutralStance)
        end
    end
    local active=c.variant~="new" or s.phase>0
    if active and t>=s.start and s.stage=="fire" and not c.firing then
        c.firing=1;SobGroup_AbilityActivate(c.source,AB_Attack,1);SobGroup_Attack(c.source_player,c.source,c.target)
        c.previous_hp=HWA_Hp(c.target)
        HWA_Log(c,"damage_fire_started","phase="..s.phase.."|level0_flag="..Player_HasResearch(c.owner,"FighterDamageLevel0"))
    end
    if active and c.firing==1 and t>=s.finish then
        c.firing=2;SobGroup_Stop(c.source_player,c.source);SobGroup_AbilityActivate(c.source,AB_Attack,0)
    end
    if active and c.firing and (c.last_sample<0 or t-c.last_sample>=0.25) then
        c.last_sample=t
        local hp=HWA_Hp(c.target);local delta=(c.previous_hp or hp)-hp;c.previous_hp=hp
        if delta>0.01 then c.hits=c.hits+1;if not c.min_hit or delta<c.min_hit then c.min_hit=delta end end
    end
    if active and t>=s.finish+4 and not c.phase_result then
        c.phase_result=1;c.metrics[s.phase+1]={damage=c.start_hp-HWA_Hp(c.target),minimum=c.min_hit or -1,hits=c.hits}
        HWA_Log(c,"damage_phase_result","phase="..s.phase.."|variant="..c.variant.."|rep="..c.rep.."|damage="..c.metrics[s.phase+1].damage.."|min_positive_delta="..(c.min_hit or -1).."|positive_samples="..c.hits.."|level1="..Player_HasResearch(c.owner,"FighterDamageLevel1").."|level2="..Player_HasResearch(c.owner,"FighterDamageLevel2"))
    end
    if s.stage=="done" or s.stage=="blocked" or t>=450 then
        local status="measured"
        if s.stage~="done" then status="blocked" end
        local first=1;if c.variant=="new" then first=2 end
        for j=first,3 do if not c.metrics[j] or c.metrics[j].hits<8 then status="blocked" end end
        HWA_Result(c,status,"variant="..c.variant.."|paid_spent="..(s.initial_ru-Player_GetRU(c.owner)).."|expected_spent=2200|finished_phase="..s.phase.."|native_family_damage_requires_control_analysis=1")
    end
end
