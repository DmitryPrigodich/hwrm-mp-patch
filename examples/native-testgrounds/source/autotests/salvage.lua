-- Native capture only: never call NoSalvageScuttle from the mission VM.
function HWS_Init(c)
    c.latched=c.id.."_latched";c.actors_group=c.id.."_actors"
    c.captured_group=c.id.."_captured"
    SobGroup_CreateIfNotExist(c.captured_group)
    SobGroup_CreateIfNotExist(c.latched);SobGroup_CreateIfNotExist(c.actors_group)
    for j=1,getn(c.actors) do
        SobGroup_SetROE(c.actors[j],PassiveROE)
        SobGroup_SobGroupAdd(c.actors_group,c.actors[j])
    end
    SobGroup_SetROE(c.target,PassiveROE);SobGroup_SetROE(c.idle,PassiveROE)
    SobGroup_AbilityActivate(c.target,AB_Attack,0);SobGroup_AbilityActivate(c.target,AB_Scuttle,c.pre_scuttle or 1)
    HWA_Freeze(c.mother);SobGroup_AbilityActivate(c.mother,AB_Move,1)
    BreakAlliance(c.owner,c.enemy);BreakAlliance(c.enemy,c.owner)
    c.base_scuttle=SobGroup_CanDoAbility(c.target,AB_Scuttle)
    c.max_latched=0;c.max_towing_actors=0;c.dock_samples=0;c.unprotected_samples=0;c.last_sample=-1
    HWA_Log(c,"salvage_baseline","scuttle="..c.base_scuttle.."|original_owner="..c.enemy.."|concurrent_idle_same_callback=1")
end

function HWS_Tick(c,t)
    if SobGroup_Count(c.target)==0 and c.action=="complete" then
        SobGroup_FilterInclude(c.captured_group,"Player_Ships"..c.owner,"ShipType","hwa_salvage_probe")
        if SobGroup_Count(c.captured_group)==1 then
            c.target=c.captured_group
            HWA_Log(c,"capture_group_rebound","ship_id_not_inferred_from_group=1|owner="..c.owner)
        end
    end
    SobGroup_GetSobGroupSalvagingGroup(c.target,c.latched)
    local latched=SobGroup_Count(c.latched)
    local owner=SobGroup_GetPlayerOwner(c.target)
    local docking=SobGroup_IsDoingAbility(c.target,AB_Dock)
    local scuttle=SobGroup_CanDoAbility(c.target,AB_Scuttle)
    local towing_actors=0
    for j=1,getn(c.actors) do
        if SobGroup_Count(c.actors[j])>0 and SobGroup_GetCurrentOrder(c.actors[j])==22 and HWA_Distance(c.actors[j],c.target)<150 and docking==1 then towing_actors=towing_actors+1 end
    end
    if latched>c.max_latched then c.max_latched=latched end
    if towing_actors>c.max_towing_actors then c.max_towing_actors=towing_actors end
    if t>=3 and not c.requested then
        c.requested=1;SobGroup_CaptureSobGroup(c.actors_group,c.target)
        HWA_Log(c,"salvage_requested","actors="..SobGroup_Count(c.actors_group))
    end
    if towing_actors>=2 and not c.latched_at then c.latched_at=t;HWA_Log(c,"native_tow_observed","docking="..docking.."|scuttle="..scuttle.."|actors_near_with_native_salcap_order="..towing_actors.."|salvaging_getter_count="..latched) end
    if c.latched_at and t-c.latched_at>=8 and docking==1 and owner==c.enemy then
        c.dock_samples=c.dock_samples+1
        if scuttle~=0 then c.unprotected_samples=c.unprotected_samples+1 end
    end
    if c.latched_at and t-c.latched_at>=12 and c.action~="complete" and not c.interrupted then
        c.interrupted=t
        if c.action=="stop" then SobGroup_Stop(c.owner,c.actors_group)
        else SobGroup_TakeDamage(c.actors_group,1) end
        HWA_Log(c,"interruption_requested","action="..c.action.."|latched="..latched.."|towing_actors="..towing_actors.."|docking="..docking.."|scuttle="..scuttle)
    end
    if owner==c.owner and not c.captured_at then
        c.captured_at=t;HWA_Log(c,"ownership_changed","owner="..owner.."|scuttle="..scuttle)
    end
    local released=c.interrupted and t-c.interrupted>=12 and latched==0 and docking==0
    local captured=c.action=="complete" and c.captured_at and t-c.captured_at>=12 and docking==0
    if released or captured then
        local status="passed"
        if scuttle~=c.base_scuttle or c.unprotected_samples>0 then status="failed" end
        HWA_Result(c,status,"action="..c.action.."|max_latched="..c.max_latched.."|max_towing_actors="..c.max_towing_actors.."|interruption_observed="..(c.interrupted and 1 or 0).."|final_owner="..owner.."|scuttle="..scuttle.."|docking="..docking.."|latched="..latched.."|tow_samples="..c.dock_samples.."|unprotected_samples="..c.unprotected_samples)
    elseif t>=180 then
        local status="blocked"
        if c.max_towing_actors>=2 and (scuttle~=c.base_scuttle and docking==0 or c.unprotected_samples>0) then status="failed" end
        HWA_Result(c,status,"reason=native_terminal_state_not_observed|action="..c.action.."|max_latched="..c.max_latched.."|final_owner="..owner.."|scuttle="..scuttle.."|docking="..docking.."|latched="..latched.."|tow_samples="..c.dock_samples.."|unprotected_samples="..c.unprotected_samples)
    end
    if not c.done and (c.last_sample<0 or t-c.last_sample>=1) then
        c.last_sample=t
        HWA_Log(c,"salvage_sample","owner="..owner.."|latched="..latched.."|docking="..docking.."|scuttle="..scuttle.."|target_real="..SobGroup_AreAllInRealSpace(c.target).."|target_selectable="..SobGroup_IsSelectable(c.target).."|distance_to_mother="..HWA_Distance(c.target,c.mother).."|actor_order="..SobGroup_GetCurrentOrder(c.actors[1]).."|actor_distance="..HWA_Distance(c.actors[1],c.target))
    end
end
