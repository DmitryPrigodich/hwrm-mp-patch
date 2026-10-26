function HWG_Init(c)
    -- Make native self-Hyperspace permission observable: no funds/enemy inhibitor gate.
    for p=0,Universe_PlayerCount()-1 do
        Player_SetRU(p,10000)
        for q=0,Universe_PlayerCount()-1 do if p~=q then SetAlliance(p,q) end end
    end
    for j=1,getn(c.sources) do SobGroup_SetROE(c.sources[j],PassiveROE) end
    SobGroup_SetROE(c.target,PassiveROE);SobGroup_AbilityActivate(c.target,AB_Attack,0);SobGroup_SetSpeed(c.target,0.75)
    c.base_move=SobGroup_CanDoAbility(c.target,AB_Move);c.base_attack=SobGroup_CanDoAbility(c.target,AB_Attack);c.base_speed=SobGroup_GetSpeed(c.target)
    c.position=SobGroup_GetPosition(c.target);c.sent={};c.releases={};c.overlaps={};c.stunned=0;c.last_sample=-1
    c.source_hyper=SobGroup_CanDoAbility(c.sources[1],AB_Hyperspace)
    HWA_Log(c,"lifecycle_baseline","move="..c.base_move.."|attack="..c.base_attack.."|speed="..c.base_speed.."|generators="..getn(c.sources).."|source_hyper="..c.source_hyper.."|allied_targets=1|native_button_api_only=1|save_load=0")
end

function HWG_Tick(c,t)
    local move=SobGroup_CanDoAbility(c.target,AB_Move)
    if move==0 then c.stunned=1 end
    local final=330
    if c.mode=="GravityToggle" then
        final=115
        for cycle=1,3 do
            local start=4+(cycle-1)*36
            for j=1,3 do
                local on=start+(j-1)*4;local off=start+12+(j-1)*4
                local key=cycle.."_"..j
                local generator=c.sources[(cycle-1)*3+j]
                if t>=on and not c.sent[key.."on"] then
                    c.sent[key.."on"]=1
                    if c.driver==1 then SobGroup_CustomCommand(generator);HWA_Log(c,"native_field_command","cycle="..cycle.."|source="..j.."|intent=on|fresh_generators_each_cycle=1") end
                end
                if t>=off and not c.sent[key.."off"] then
                    c.sent[key.."off"]=1
                    if c.driver==1 then SobGroup_CustomCommand(generator);HWA_Log(c,"native_field_command","cycle="..cycle.."|source="..j.."|intent=off") end
                end
            end
            if t>=start+19 and not c.overlaps[cycle] then c.overlaps[cycle]=1-move;HWA_Log(c,"lifecycle_overlap","cycle="..cycle.."|move="..move) end
            if t>=start+25 and not c.releases[cycle] then c.releases[cycle]=1+move;HWA_Log(c,"lifecycle_release","cycle="..cycle.."|move="..move) end
        end
        if t>=104 and move==c.base_move and not c.move_sent then c.move_sent=1;SobGroup_Move(c.owner,c.target,c.destination) end
    else
        if t>=4 and not c.started then
            c.started=1
            if c.driver==1 then SobGroup_CustomCommand(c.sources[1]);HWA_Log(c,"native_field_command","intent=on|await_natural_completion=1") end
        end
        local ended=SobGroup_Count(c.sources[1])==0 or c.source_hyper==1 and SobGroup_CanDoAbility(c.sources[1],AB_Hyperspace)==1
        local inside=SobGroup_Count(c.sources[1])==0 or HWA_Distance(c.target,c.sources[1])<2500
        if t>=12 and c.stunned==1 and move==c.base_move and ended and inside and not c.natural_release then
            c.natural_release=t;c.move_sent=1;SobGroup_Move(c.owner,c.target,c.destination)
            HWA_Log(c,"natural_release_observed","move="..move.."|generator_alive="..SobGroup_Count(c.sources[1]))
        end
        if c.natural_release and t-c.natural_release>=12 then final=t end
    end
    if c.last_sample<0 or t-c.last_sample>=2 then
        c.last_sample=t
        HWA_Log(c,"lifecycle_sample","move="..move.."|attack="..SobGroup_CanDoAbility(c.target,AB_Attack).."|speed="..SobGroup_GetSpeed(c.target).."|generator_alive="..SobGroup_Count(c.sources[1]).."|source_hyper="..SobGroup_CanDoAbility(c.sources[1],AB_Hyperspace).."|distance="..HWA_Distance(c.target,c.sources[1]))
    end
    if t>=final then
        local p=SobGroup_GetPosition(c.target);local distance=sqrt((p[1]-c.position[1])^2+(p[2]-c.position[2])^2+(p[3]-c.position[3])^2)
        local status="blocked";local cycles=1
        if c.mode=="GravityToggle" then cycles=3 end
        local good=c.stunned==1 and move==c.base_move and SobGroup_CanDoAbility(c.target,AB_Attack)==c.base_attack and SobGroup_GetSpeed(c.target)==c.base_speed and distance>100
        if c.mode=="GravityToggle" then for j=1,3 do if c.releases[j]~=2 or c.overlaps[j]~=1 then good=nil end end end
        if good then status="passed" end
        HWA_Result(c,status,"mode="..c.mode.."|cycles="..cycles.."|stunned="..c.stunned.."|final_move="..move.."|attack="..SobGroup_CanDoAbility(c.target,AB_Attack).."|speed="..SobGroup_GetSpeed(c.target).."|distance_after_release="..distance.."|natural_release="..(c.natural_release or -1).."|unobserved_release_is_not_automatically_a_patch_bug=1")
    end
end
