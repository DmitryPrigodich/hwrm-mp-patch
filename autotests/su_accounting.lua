-- Diagnostic only: exact nominal counts, native getters, no production requests.
function SUA_Log(event, text)
    print("HWMP_SUACC|token="..SUA_Token.."|world="..SUA_World.."|event="..event.."|"..(text or ""))
end

function SUA_Used(player)
    local total=0
    for ship,cost in HWMP_CataclysmCosts do
        total=total+cost*Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(player,ship)
    end
    return total
end

function SUA_Spawn(c, ship, number)
    local group="SUA_"..c.player.."_"..number
    SobGroup_CreateIfNotExist(group)
    SobGroup_SpawnNewShipInSobGroup(c.player,ship,group,group,"SUB_Volume"..c.player)
    SobGroup_AbilityActivate(group,AB_Move,0)
    SobGroup_AbilityActivate(group,AB_Attack,0)
    SobGroup_AbilityActivate(group,AB_Targeting,0)
    SobGroup_AbilityActivate(group,AB_Builder,0)
    SobGroup_SetInvulnerability(group,1)
end

function SUB_Init()
    Rule_Remove("SUB_Init")
    for p=0,Universe_PlayerCount()-1 do
        CPU_Enable(p,0)
        for q=0,Universe_PlayerCount()-1 do if p~=q then SetAlliance(p,q) end end
    end
    for i,c in SUA_Cases do
        Player_SetRU(c.player,100000)
        SobGroup_AbilityActivate("SUB_Mother"..c.player,AB_Builder,0)
        for j=1,2 do
            local group="SUB_Carrier"..c.player.."A"
            if j==2 then group="SUB_Carrier"..c.player.."B" end
            SobGroup_CreateSubSystem(group,"FighterProduction")
        end
        CPU_DoString(c.player,"sg_dobuild=0;sg_dosubsystems=0;sg_doresearch=0;sg_doupgrades=0;sg_domilitary=0;cp_processResource=0;cp_processMilitary=0")
        CPU_Enable(c.player,1)
        c.count=0
    end
    if SUA_Mode~="measure" and strlower(tostring(GetGameSettingAsString("unitcaps")))~="normal" then
        SUA_Log("blocked","reason=normal_profile_required")
        SUA_Log("end","acceptance=blocked")
        return
    end
    SUA_Step=0
    SUA_Log("setup","scale="..SUA_Scale.."|mode="..SUA_Mode.."|build_requests=0")
    Rule_AddInterval("SUA_SpawnStep",3)
end

function SUA_SpawnStep()
    Rule_Remove("SUA_SpawnStep")
    SUA_Step=SUA_Step+1
    for i,c in SUA_Cases do
        if SUA_Mode~="measure" then
            for j,ship in c.plan do SUA_Spawn(c,ship,j) end
            c.count=getn(c.plan)
        else
            local target=SUA_Counts[SUA_Step]
            if c.unbounded~=1 and target>16 then target=16 end
            for j=c.count+1,target do SUA_Spawn(c,c.ship,j) end
            c.count=target
        end
    end
    Rule_AddInterval("SUA_ReadStep",2)
end

function SUA_ReadStep()
    Rule_Remove("SUA_ReadStep")
    for i,c in SUA_Cases do
        local used=SUA_Used(c.player)
        local expected=80
        if SUA_Mode~="measure" then expected=SUA_EqualNominal else expected=80+c.count*c.cost end
        local observed=0
        if SUA_Mode=="measure" then observed=Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(c.player,c.ship)
        else
            for ship,n in c.inventory do
                observed=observed+Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(c.player,ship)
            end
        end
        SUA_Log("owned","case="..c.id.."|step="..SUA_Step.."|entries="..observed.."|expected_entries="..c.count.."|nominal="..used.."|expected="..expected.."|valid="..tostring(used==expected and observed==c.count))
        local query=gsub(c.query,"STEP",tostring(SUA_Step))
        CPU_DoString(c.player,query)
    end
    if SUA_Mode=="equalbuild" then
        SUA_ProductionT0=Universe_GameTime()
        for i,c in SUA_Cases do c.sent=0;c.last="" end
        Rule_AddInterval("SUA_Production",1)
    elseif SUA_Mode=="equal" or SUA_Step==getn(SUA_Counts) then
        SUA_Log("end","production_test=0|physical_hulls_verified=0")
    else Rule_AddInterval("SUA_SpawnStep",1) end
end

function SUA_Production()
    local elapsed=Universe_GameTime()-SUA_ProductionT0
    for i,c in SUA_Cases do
        local count=Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(c.player,"hgn_interceptor")
        local used=SUA_Used(c.player)
        local ru=Player_GetRU(c.player)
        local sample=count..":"..used..":"..ru
        if sample~=c.last then
            SUA_Log("paid","case="..c.id.."|completed="..count.."|nominal="..used.."|ru="..ru.."|backend=guarded_CPU_NOT_UI")
            c.last=sample
        end
        if c.sent<2 and count>=c.sent then
            c.sent=c.sent+1
            CPU_DoString(c.player,c.query)
            local tag="HWMP_SUACC|token="..SUA_Token.."|world="..SUA_World.."|event=admit|case="..c.id.."|request="..c.sent
            local code='local allowed=CanBuild(HGN_INTERCEPTOR); print("'..tag..'|can="..allowed); if allowed==1 then Build(HGN_INTERCEPTOR) end'
            CPU_DoString(c.player,code)
        end
    end
    if elapsed>=100 then
        for i,c in SUA_Cases do
            SUA_Log("production_result","case="..c.id.."|completed="..Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(c.player,"hgn_interceptor").."|nominal="..SUA_Used(c.player).."|ru="..Player_GetRU(c.player))
        end
        SUA_Log("end","production_test=1|guarded_CPU_NOT_UI=1|cross_producer_test=0")
        Rule_Remove("SUA_Production")
    end
end
