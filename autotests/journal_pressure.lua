function HWP_Init(c)
    c.last_sample=-1;c.bad_overlap=0;c.origins={}
    for p=0,Universe_PlayerCount()-1 do
        for q=0,Universe_PlayerCount()-1 do if p~=q then SetAlliance(p,q) end end
    end
    for i=1,getn(c.members) do
        local g=c.members[i];HWA_Freeze(g);SobGroup_AbilityActivate(g,AB_Move,1)
        SobGroup_AbilityActivate(g,AB_Attack,mod(i,2));SobGroup_SetSpeed(g,mod(i,2)==1 and 0.75 or 1)
    end
    HWA_Log(c,"pressure_baseline","configured_entries="..getn(c.members).."|physical_hulls_inferred=0|clock_available="..type(clock))
end
function HWP_Tick(c,t)
    for i=1,3 do
        if t>=i+1 and not c["on"..i] then c["on"..i]=1;SobGroup_CustomCommand(c.sources[i]) end
        if t>=6+i*4 and not c["killed"..i] then c["killed"..i]=1;SobGroup_TakeDamage(c.sources[i],1) end
    end
    if t>=6 and not c.steady then
        c.steady=1;if clock then c.cpu_start=clock() end
        HWA_Log(c,"pressure_steady","configured_entries="..getn(c.members))
    end
    if t>=15 and not c.checked then
        c.checked=1
        for i=1,getn(c.members) do if SobGroup_CanDoAbility(c.members[i],AB_Move)~=0 then c.bad_overlap=c.bad_overlap+1 end end
    end
    if t>=20 and not c.moved then
        c.moved=1
        for i=1,getn(c.members) do
            local g=c.members[i];c.origins[i]=SobGroup_GetPosition(g)
            SobGroup_Move(SobGroup_GetPlayerOwner(g),g,c.volume)
        end
    end
    if t>=26 then
        local bad=0;local minimum=100000
        for i=1,getn(c.members) do
            local g=c.members[i];local expected=mod(i,2)==1 and 0.75 or 1
            if SobGroup_CanDoAbility(g,AB_Move)~=1 or SobGroup_CanDoAbility(g,AB_Attack)~=mod(i,2) or abs(SobGroup_GetSpeed(g)-expected)>0.000001 then bad=bad+1 end
            local p=SobGroup_GetPosition(g);local q=c.origins[i]
            minimum=min(minimum,sqrt((p[1]-q[1])^2+(p[2]-q[2])^2+(p[3]-q[3])^2))
        end
        local cpu=-1;if clock and c.cpu_start then cpu=clock()-c.cpu_start end
        local status="passed";if bad>0 or c.bad_overlap>0 or minimum<300 then status="failed" end
        HWA_Result(c,status,"configured_entries="..getn(c.members).."|wrong_restoration="..bad.."|early_release="..c.bad_overlap.."|minimum_movement="..minimum.."|cpu_window="..cpu)
    end
end
