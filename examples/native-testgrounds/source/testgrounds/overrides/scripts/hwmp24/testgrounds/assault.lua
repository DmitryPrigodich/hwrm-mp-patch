dofilepath("data:scripts/SCAR/SCAR_Util.lua")
dofilepath("data:scripts/hwmp24/testgrounds/version.lua")
dofilepath("data:scripts/hwmp24/testgrounds/common.lua")

function HWT_AssaultStart()
    if HWT_STARTED == 1 then return end
    HWT_STARTED = 1
    HWT_START = Universe_GameTime()
    HWT_Log("start", "duration=45|shooter_move=0|target_attack=0|upgrade_player=2")
    for i = 1, 4 do
        SobGroup_Move(HWT_TARGET_PLAYER[i], "HWT_Target" .. i, "HWT_Retreat" .. i)
        SobGroup_Attack(0, "HWT_Assault" .. i, "HWT_Target" .. i)
    end
    Subtitle_Message("$9984023", 20)
end

function HWT_ScenarioTick()
    for i = 1, 4 do HWT_Distance("HWT_Assault" .. i, "HWT_Target" .. i) end
    if HWT_STARTED == 1 and Universe_GameTime() - HWT_START >= 45 then
        for i = 1, 4 do
            SobGroup_Stop(0, "HWT_Assault" .. i)
            SobGroup_AbilityActivate("HWT_Assault" .. i, AB_Attack, 0)
        end
        HWT_Complete()
    end
end

function OnInit()
    CPU_Enable(2, 0)
    HWT_Init("assault", "$9984021", {
        "HWT_Assault1", "HWT_Assault2", "HWT_Assault3", "HWT_Assault4",
        "HWT_Target1", "HWT_Target2", "HWT_Target3", "HWT_Target4"
    })
    HWT_TARGET_PLAYER = {1, 1, 2, 2}
    Player_UnrestrictResearchOption(2, "InterceptorMAXSPEEDUpgrade1")
    Player_GrantResearchOption(2, "InterceptorMAXSPEEDUpgrade1")
    for i = 1, 4 do
        SobGroup_AbilityActivate("HWT_Assault" .. i, AB_Move, 0)
        SobGroup_AbilityActivate("HWT_Target" .. i, AB_Attack, 0)
        SobGroup_SetStance("HWT_Assault" .. i, NeutralStance)
        SobGroup_SetStance("HWT_Target" .. i, NeutralStance)
        if i == 2 or i == 4 then SobGroup_SetStance("HWT_Target" .. i, EvasiveStance) end
        HWT_Log("lane", "index=" .. i .. "|target_player=" .. HWT_TARGET_PLAYER[i] .. "|evasive=" .. mod(i+1, 2))
    end
    HWT_Log("upgrade", "player=2|name=InterceptorMAXSPEEDUpgrade1|grant_requested=1|application=requires_native_observation")
    UI_BindKeyEvent(ONEKEY, "HWT_AssaultStart")
end
