-- Test-only. Spawn is used solely for baseline padding, never for the requested build.
function SUB_Log(event, text)
    print("HWMP_SUB|world=" .. SUB_World .. "|t=" .. Universe_GameTime() .. "|event=" .. event .. "|" .. (text or ""))
end

function SUB_Used(player)
    local total=0
    for ship,cost in HWMP_CataclysmCosts do
        total=total+cost*Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(player,ship)
    end
    return total
end

function SUB_Init()
    Rule_Remove("SUB_Init")
    SUB_T0=Universe_GameTime()
    local profile=strlower(tostring(GetGameSettingAsString("unitcaps")))
    SUB_Budget=HWMP_CataclysmBudgets[profile]
    if SUB_Budget==nil then SUB_Log("blocked","reason=unknown_unitcap_profile");return end
    for p=0,Universe_PlayerCount()-1 do
        CPU_Enable(p,0)
        for q=0,Universe_PlayerCount()-1 do if p~=q then SetAlliance(p,q) end end
    end
    for i,c in SUB_Cases do
        c.base_count=Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(c.player,SUB_Item)
        Player_SetRU(c.player,100000)
        if SUB_HW1==1 then Player_GrantResearchOption(c.player,"FighterChassis")
        else
            for j,group in c.builders do SobGroup_CreateSubSystem(group,"FighterProduction") end
        end
        SobGroup_AbilityActivate(c.mother,AB_Builder,0)
        local plan=SUB_Padding[profile][c.id]
        for j,ship in plan do
            local group="SUB_Pad"..c.player.."_"..j
            SobGroup_CreateIfNotExist(group)
            SobGroup_SpawnNewShipInSobGroup(c.player,ship,group,group,c.volume)
            SobGroup_AbilityActivate(group,AB_Move,0)
            SobGroup_AbilityActivate(group,AB_Attack,0)
            SobGroup_AbilityActivate(group,AB_Targeting,0)
            SobGroup_AbilityActivate(group,AB_Builder,0)
            SobGroup_SetInvulnerability(group,1)
        end
        c.expected=SUB_Budget-c.free
        c.last="";c.max_building=0;c.max_delta=0;c.started=0
    end
    SUB_Log("setup","profile="..profile.."|budget="..SUB_Budget.."|item="..SUB_Item.."|cost="..SUB_Cost.."|setup_spawns_not_production=1")
    Rule_AddInterval("SUB_Observe",0.25)
    Rule_AddInterval("SUB_Request",5)
    if SUB_Auto==0 then
        SobGroup_SelectSobGroup(SUB_Cases[1].builders[1])
        UI_ShowScreen("NewBuildMenu",0)
        Subtitle_Message("$9988001",120)
    end
end

function SUB_Request()
    Rule_Remove("SUB_Request")
    for i,c in SUB_Cases do
        c.base_count=Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(c.player,SUB_Item)
        c.start_ru=Player_GetRU(c.player)
        c.actual=SUB_Used(c.player)
        c.valid=c.actual==c.expected
        SUB_Log("baseline","case="..c.id.."|player="..c.player.."|used="..c.actual.."|expected="..c.expected.."|free="..c.free.."|valid="..tostring(c.valid))
        if SUB_Auto==1 and c.valid then
            if CPU_DoString==nil or CPU_Exist==nil or CPU_Exist(c.player)~=1 then
                c.valid=nil;SUB_Log("blocked","case="..c.id.."|reason=no_AI_context")
            else
                CPU_DoString(c.player,"sg_dobuild=0;sg_dosubsystems=0;sg_doresearch=0;sg_doupgrades=0;sg_domilitary=0;cp_processResource=0;cp_processMilitary=0")
                CPU_Enable(c.player,1)
                local code='print("HWMP_SUB_AI|case='..c.id..'|Build="..type(Build).."|CanBuild="..type(CanBuild)); if type(Build)=="function" and type(CanBuild)=="function" and type('..SUB_ItemID..')=="number" then '
                code=code..'print("HWMP_SUB_AI|case='..c.id..'|can="..CanBuild('..SUB_ItemID..')); '
                for j=1,c.requests do code=code..'Build('..SUB_ItemID..'); ' end
                code=code..'end'
                CPU_DoString(c.player,code)
                SUB_Log("request","case="..c.id.."|count="..c.requests.."|backend=CPU_Build_NOT_UI")
            end
        end
    end
end

function SUB_Observe()
    for i,c in SUB_Cases do
        local used=SUB_Used(c.player)
        local delta=Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(c.player,SUB_Item)-c.base_count
        local active=0
        local flags=""
        for j,group in c.builders do
            local building=SobGroup_IsBuilding(group,SUB_Item)
            active=active+building;flags=flags..building
        end
        local ru=Player_GetRU(c.player)
        local queued=Player_HasQueuedBuild(c.player,SUB_Item)
        local sample=used..":"..delta..":"..flags..":"..queued..":"..ru
        if sample~=c.last then
            SUB_Log("sample","case="..c.id.."|used="..used.."|delta="..delta.."|builders="..flags.."|queued="..queued.."|ru="..ru)
            c.last=sample
        end
        if active>c.max_building then c.max_building=active end
        if delta>c.max_delta then c.max_delta=delta end
        if delta>0 or (c.start_ru~=nil and ru<c.start_ru) then c.started=1 end
    end
    if SUB_Auto==1 and Universe_GameTime()-SUB_T0>=100 then
        local control=SUB_Cases[1].max_delta>=1
        -- IsBuilding also reports waiting queues; it cannot prove concurrent progress.
        local concurrency=nil
        for i,c in SUB_Cases do
            local result="passed"
            if not c.valid or not control then result="blocked" end
            if c.free<SUB_Cost and (c.max_delta>0 or c.started==1) then result="failed" end
            if c.free>=SUB_Cost and c.max_delta<1 then result="blocked" end
            if c.requests==2 then
                if result=="passed" then result="blocked_producer_progress_unverified" end
                if c.max_delta*SUB_Cost>c.free then result="failed" end
            end
            SUB_Log("result","case="..c.id.."|status="..result.."|max_delta="..c.max_delta.."|max_active="..c.max_building.."|positive_control="..tostring(control).."|cross_producer_control="..tostring(concurrency))
        end
        SUB_Log("end","manual_cancel_pause_destroy_still_required=1")
        Rule_Remove("SUB_Observe")
    end
end
