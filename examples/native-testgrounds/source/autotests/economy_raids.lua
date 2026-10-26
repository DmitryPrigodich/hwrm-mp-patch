function HWR_Init(c)
    HWA_Freeze(c.receiver);SobGroup_SetInvulnerability(c.receiver,1)
    if c.backup~="" then HWA_Freeze(c.backup);SobGroup_SetInvulnerability(c.backup,1) end
    SobGroup_CreateIfNotExist(c.id)
    for j=1,getn(c.members) do SobGroup_SobGroupAdd(c.id,c.members[j]) end
    c.initial_ru=Player_GetRU(c.player);c.raids={};c.last_sample=-1;c.previous_ru=c.initial_ru
    HWA_Log(c,"raids_baseline","collectors=6|receiver="..c.receiver_type.."|alternate_receiver="..c.backup.."|ru="..c.initial_ru.."|scripted_subsystem_damage_not_enemy_wave=1")
end

function HWR_Tick(c,t)
    if t>=5 and not c.started then c.started=1;SobGroup_Resource(c.player,c.id) end
    for j=1,getn(c.damage_times) do
        if t>=c.damage_times[j] and not c.raids[j] then
            c.raids[j]={at=t,ru=Player_GetRU(c.player)};SobGroup_SetHardPointHealth(c.receiver,"Resource",0)
            HWA_Log(c,"raid_hit","raid="..j.."|resource_hp="..SobGroup_GetHardPointHealth(c.receiver,"Resource").."|ru="..Player_GetRU(c.player))
        end
    end
    if c.last_sample<0 or t-c.last_sample>=1 then
        c.last_sample=t
        local ru=Player_GetRU(c.player);local hp=SobGroup_GetHardPointHealth(c.receiver,"Resource")
        for j=1,getn(c.raids) do
            local r=c.raids[j]
            if t>=r.at and (j==getn(c.raids)) then
                if hp<0.001 then r.zero_seen=1 end
                if r.zero_seen==1 and hp>0.001 and not r.first_regen then r.first_regen=t;HWA_Log(c,"raid_regeneration","raid="..j.."|hp="..hp.."|since_hit="..(t-r.at)) end
                if hp>=0.05 and not r.five then r.five=t;HWA_Log(c,"raid_five_percent","raid="..j.."|since_hit="..(t-r.at)) end
                if ru>c.previous_ru then
                    if not r.first_credit then r.first_credit=t;HWA_Log(c,"raid_first_credit","raid="..j.."|since_hit="..(t-r.at).."|resource_hp="..hp.."|unload_in_flight_possible=1") end
                    r.last_credit=t;r.credit_events=(r.credit_events or 0)+1
                end
            end
        end
        c.previous_ru=ru
        HWA_Log(c,"raids_sample","ru="..ru.."|receiver_hp="..hp.."|collectors="..SobGroup_Count(c.id))
    end
    if t>=c.finish then
        local status="measured"
        if Player_GetRU(c.player)<=c.initial_ru or getn(c.raids)~=3 then status="blocked" end
        for j=1,3 do
            local r=c.raids[j] or {}
            HWA_Log(c,"raid_result","raid="..j.."|zero_seen="..(r.zero_seen or 0).."|first_regen="..(r.first_regen or -1).."|five_percent="..(r.five or -1).."|first_credit="..(r.first_credit or -1).."|last_credit="..(r.last_credit or -1).."|credit_events="..(r.credit_events or 0))
        end
        HWA_Result(c,status,"income="..(Player_GetRU(c.player)-c.initial_ru).."|collectors="..SobGroup_Count(c.id).."|window=720|raids=3|receiver="..c.receiver_type.."|alternative="..(c.backup~="" and 1 or 0).."|scripted_knockouts_not_full_raid_balance=1")
    end
end
