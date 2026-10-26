-- Native SCAR harness. Measurements are observations, not an engine verdict.
-- Keep numeric lists separate from record fields for the native Lua 4 parser.
function HWT_Log(event, fields)
    print("HWMP_TEST|v=1|suite=" .. HWT_REVISION .. "|mission=" .. HWT_MISSION ..
        "|t=" .. Universe_GameTime() .. "|event=" .. event .. "|" .. (fields or ""))
end

function HWT_Sample(group)
    local entries = SobGroup_Count(group)
    local fields = "group=" .. group .. "|entries=" .. entries
    if entries > 0 then
        local p = SobGroup_GetPosition(group)
        fields = fields .. "|x=" .. p[1] .. "|y=" .. p[2] .. "|z=" .. p[3] ..
            "|hp_fraction=" .. SobGroup_HealthPercentage(group) ..
            "|move=" .. SobGroup_CanDoAbility(group, AB_Move) ..
            "|attack=" .. SobGroup_CanDoAbility(group, AB_Attack) ..
            "|dock=" .. SobGroup_CanDoAbility(group, AB_Dock) ..
            "|custom=" .. SobGroup_CanDoAbility(group, AB_Custom)
        -- Optional API: never use the square-speed API as a speed in m/s.
        if SobGroup_CurrentHealthTotal then
            fields = fields .. "|hp_total=" .. SobGroup_CurrentHealthTotal(group)
        end
        local old = HWT_PREVIOUS[group]
        local now = Universe_GameTime()
        if old and now > old.t then
            local dx = p[1] - old.x
            local dy = p[2] - old.y
            local dz = p[3] - old.z
            fields = fields .. "|centroid_speed=" .. sqrt(dx*dx + dy*dy + dz*dz)/(now-old.t)
        end
        HWT_PREVIOUS[group] = {x=p[1], y=p[2], z=p[3], t=now}
    end
    HWT_Log("sample", fields)
end

function HWT_Distance(a, b)
    if SobGroup_Count(a) == 0 or SobGroup_Count(b) == 0 then return end
    local p = SobGroup_GetPosition(a)
    local q = SobGroup_GetPosition(b)
    local dx = p[1]-q[1]
    local dy = p[2]-q[2]
    local dz = p[3]-q[3]
    HWT_Log("distance", "a=" .. a .. "|b=" .. b .. "|metres=" .. sqrt(dx*dx+dy*dy+dz*dz))
end

function HWT_Help()
    Subtitle_Message(HWT_HELP, 30)
end

function HWT_Init(mission, help, groups)
    HWT_MISSION = mission
    HWT_HELP = help
    HWT_GROUPS = groups
    HWT_PREVIOUS = {}
    HWT_STARTED = 0
    HWT_DONE = 0
    CPU_Enable(1, 0)
    SobGroup_SetInvulnerability("HWT_Anchor", 1)
    SobGroup_SetROE("HWT_Anchor", PassiveROE)
    SobGroup_AbilityActivate("HWT_Anchor", AB_Builder, 0)
    SobGroup_AbilityActivate("HWT_Anchor", AB_Move, 0)
    for i = 1, getn(groups) do
        FOW_RevealGroup(groups[i], 1)
        SobGroup_SetROE(groups[i], PassiveROE)
    end
    Camera_Interpolate("here", "HWT_Home", 0)
    HWT_OBJECTIVE = Objective_Add("$9984002", OT_Primary)
    Objective_AddDescription(HWT_OBJECTIVE, help)
    UI_BindKeyEvent(THREEKEY, "HWT_Help")
    HWT_Help()
    HWT_Log("init", "native_status=not_evaluated|counts=squadron_entries")
    Rule_AddInterval("HWT_Tick", 1)
end

function HWT_Tick()
    for i = 1, getn(HWT_GROUPS) do HWT_Sample(HWT_GROUPS[i]) end
    HWT_ScenarioTick()
end

function HWT_Complete()
    if HWT_DONE == 1 then return end
    HWT_DONE = 1
    HWT_Log("finished", "verdict=observation_only")
    Subtitle_Message("$9984003", 20)
    Objective_SetState(HWT_OBJECTIVE, OS_Complete)
    Rule_Remove("HWT_Tick")
    -- Remain in the arena for inspection/save. Restart through the mission menu.
end
