-- Native transport lifecycle. Never call the patched transport helper directly.
function HWT_Init(c)
    SobGroup_SetROE(c.carrier,PassiveROE)
    SobGroup_AbilityActivate(c.carrier,AB_Attack,0)
    c.baselines={};c.last_sample=-1
    for j=1,getn(c.members) do
        local g=c.members[j]
        SobGroup_SetROE(g,PassiveROE)
        SobGroup_AbilityActivate(g,AB_Attack,j-1)
        SobGroup_AbilityActivate(g,AB_Scuttle,j-1)
        SobGroup_SetSpeed(g,0.5+j*0.25)
        c.baselines[j]={attack=SobGroup_CanDoAbility(g,AB_Attack),dock=SobGroup_CanDoAbility(g,AB_Dock),scuttle=SobGroup_CanDoAbility(g,AB_Scuttle),speed=SobGroup_GetSpeed(g),selectable=SobGroup_IsSelectable(g)}
        HWA_Log(c,"passenger_baseline","member="..j.."|attack="..c.baselines[j].attack.."|dock="..c.baselines[j].dock.."|scuttle="..c.baselines[j].scuttle.."|speed="..c.baselines[j].speed)
    end
end

function HWT_Tick(c,t)
    if not SobGroup_EnterHyperSpaceOffMap or not SobGroup_ExitHyperSpace or not SobGroup_IsSelectable then
        HWA_Result(c,"blocked","reason=required_native_transport_API_unavailable");return
    end
    local docked=0;local alive=0;local restored=0;local selectable=0;local outside=0;local real=0;local hyper=0
    for j=1,getn(c.members) do
        local g=c.members[j]
        if SobGroup_Count(g)>0 then
            alive=alive+1
            if SobGroup_AreAllInRealSpace(g)==1 then real=real+1 end
            if SobGroup_AreAllInHyperspace(g)==1 then hyper=hyper+1 end
            if SobGroup_IsDocked(g)==1 then docked=docked+1 else outside=outside+1 end
            if SobGroup_IsSelectable(g)==c.baselines[j].selectable then selectable=selectable+1 end
            if SobGroup_CanDoAbility(g,AB_Attack)==c.baselines[j].attack and SobGroup_CanDoAbility(g,AB_Dock)==c.baselines[j].dock and
               SobGroup_CanDoAbility(g,AB_Scuttle)==c.baselines[j].scuttle and SobGroup_GetSpeed(g)==c.baselines[j].speed then restored=restored+1 end
        end
    end
    if t>=3 and not c.dock_requested then
        c.dock_requested=1
        for j=1,getn(c.members) do SobGroup_DockSobGroupAndStayDocked(c.members[j],c.carrier) end
        HWA_Log(c,"dock_requested","members="..getn(c.members))
    end
    if docked==getn(c.members) and not c.enter_requested then
        c.enter_requested=1;c.docked_at=t
        SobGroup_EnterHyperSpaceOffMap(c.carrier)
        HWA_Log(c,"enter_requested","docked_members="..docked.."|native_hyperspace=1|fixture=scripted_offmap_and_exit")
    end
    if c.enter_requested and SobGroup_AreAllInRealSpace(c.carrier)==0 and not c.transition_seen then
        c.transition_seen=1;c.transition_at=t
        HWA_Log(c,"transition_observed","in_hyperspace="..SobGroup_AreAllInHyperspace(c.carrier).."|passengers_alive="..alive.."|selectable="..selectable)
    end
    if c.enter_requested and c.action=="stop" and not c.stop_requested then
        local previous=SobGroup_GetCurrentOrder(c.carrier)
        c.stop_requested=1;c.stop_at=t;SobGroup_Stop(c.owner,c.carrier)
        HWA_Log(c,"stop_requested","phase=entry|previous_order="..previous.."|new_order="..SobGroup_GetCurrentOrder(c.carrier))
    end
    if c.stop_at and not c.full_hyper_at and t-c.stop_at>=4 and SobGroup_AreAllInRealSpace(c.carrier)==1 and not c.launch_requested then
        c.charge_cancelled=1;c.launch_requested=1;SobGroup_SetROE(c.carrier,OffensiveROE)
        HWA_Log(c,"charge_cancelled","carrier_real=1|launch_via=native_offensive_ROE_callback")
    end
    if c.transition_seen and SobGroup_AreAllInHyperspace(c.carrier)==1 and not c.full_hyper_at then
        c.full_hyper_at=t;HWA_Log(c,"full_hyperspace","passengers_alive="..alive.."|selectable="..selectable)
    end
    if c.full_hyper_at and t-c.full_hyper_at>=3 and not c.exit_requested and not c.destroy_requested then
        if c.action=="destroy" then
            c.destroy_requested=1;SobGroup_TakeDamage(c.carrier,1)
            HWA_Log(c,"carrier_destroy_requested","phase=full_hyperspace")
        else
            c.exit_requested=1;SobGroup_ExitHyperSpace(c.carrier,c.destination)
            HWA_Log(c,"exit_requested","volume="..c.destination)
        end
    end
    if c.exit_requested and SobGroup_AreAllInRealSpace(c.carrier)==1 then
        if not c.returned_at then c.returned_at=t;HWA_Log(c,"carrier_returned","docked_members="..docked.."|alive_members="..alive) end
        if t-c.returned_at>=4 and not c.launch_requested then
            c.launch_requested=1
            SobGroup_SetROE(c.carrier,OffensiveROE)
            HWA_Log(c,"launch_requested","via=native_offensive_ROE_callback|alive_members="..alive.."|restored="..restored.."|selectable="..selectable)
        end
    end
    if c.launch_requested and real==getn(c.members) and outside==getn(c.members) and restored==getn(c.members) and selectable==getn(c.members) then
        HWA_Result(c,"passed","native_dock=1|transition_seen="..(c.transition_seen or 0).."|restored_members="..restored.."|selectable_members="..selectable.."|action="..c.action.."|stop_cancelled_transition="..(c.charge_cancelled or 0))
    elseif c.destroy_requested and SobGroup_Count(c.carrier)==0 and t-c.full_hyper_at>=8 then
        local status="measured"
        if alive>0 then
            if restored==alive and selectable==alive and real==alive then status="passed" else status="failed" end
        end
        HWA_Result(c,status,"carrier_dead=1|survivor_groups="..alive.."|survivor_real="..real.."|survivor_hyper="..hyper.."|restored_survivors="..restored.."|selectable_survivors="..selectable.."|owner_scout_squadrons="..Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(c.owner,c.member_types[1]).."|owner_corvette_squadrons="..Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(c.owner,c.member_types[2]).."|passenger_loss_policy=not_decided")
    elseif t>=100 then
        local status="failed"
        if not c.transition_seen then status="blocked" end
        HWA_Result(c,status,"docked_members="..docked.."|alive_members="..alive.."|outside_members="..outside.."|restored_members="..restored.."|selectable_members="..selectable.."|transition_seen="..(c.transition_seen or 0).."|exit_requested="..(c.exit_requested or 0).."|launch_requested="..(c.launch_requested or 0))
    end
    if not c.done and (c.last_sample<0 or t-c.last_sample>=1) then
        c.last_sample=t
        HWA_Log(c,"transport_sample","docked_members="..docked.."|alive_members="..alive.."|restored_members="..restored.."|selectable_members="..selectable.."|carrier_real="..SobGroup_AreAllInRealSpace(c.carrier).."|carrier_hyper="..SobGroup_AreAllInHyperspace(c.carrier))
        for j=1,getn(c.members) do
            local g=c.members[j]
            if SobGroup_Count(g)>0 then
                HWA_Log(c,"passenger_sample","member="..j.."|docked="..SobGroup_IsDocked(g).."|docking="..SobGroup_IsDoingAbility(g,AB_Dock).."|real="..SobGroup_AreAllInRealSpace(g).."|hyper="..SobGroup_AreAllInHyperspace(g).."|attack="..SobGroup_CanDoAbility(g,AB_Attack).."|dock="..SobGroup_CanDoAbility(g,AB_Dock).."|scuttle="..SobGroup_CanDoAbility(g,AB_Scuttle).."|speed="..SobGroup_GetSpeed(g).."|selectable="..SobGroup_IsSelectable(g))
            end
        end
    end
end
