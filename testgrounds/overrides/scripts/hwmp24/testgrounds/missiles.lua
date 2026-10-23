dofilepath("data:scripts/SCAR/SCAR_Util.lua")
dofilepath("data:scripts/hwmp24/testgrounds/version.lua")
dofilepath("data:scripts/hwmp24/testgrounds/common.lua")

function HWT_MissileCount(event)
    if Selection_Create and Selection_GetMissiles then
        if HWT_SELECTION_READY == 0 then
            Selection_Create("HWT_Missiles")
            HWT_SELECTION_READY = 1
        end
        HWT_Log(event, "universe_missiles=" .. Selection_GetMissiles("HWT_Missiles") .. "|identity=unknown")
    else
        HWT_Log(event, "universe_missiles=unavailable|identity=unknown")
    end
end

function HWT_MissileStart()
    if HWT_STARTED == 1 then return end
    HWT_STARTED = 1
    HWT_START = Universe_GameTime()
    SobGroup_Attack(0, "HWT_Launcher", "HWT_Primary")
    HWT_Log("start", "launcher=vgr_heavymissilefrigate|primary=hgn_torpedofrigate|replacement=hgn_torpedofrigate")
    Subtitle_Message("$9984033", 25)
end

function HWT_MissileKill()
    if HWT_STARTED == 0 or HWT_KILLED == 1 or HWT_DONE == 1 then return end
    if SobGroup_Count("HWT_Primary") == 0 then
        HWT_Log("blocked", "reason=primary_already_dead_before_operator_trigger")
        return
    end
    HWT_MissileCount("before_target_loss")
    HWT_KILLED = 1
    HWT_KILL_TIME = Universe_GameTime()
    -- Explicit intervention, logged as such: prevent further launches before
    -- removing the primary. Never attribute replacement damage to retargeting
    -- automatically; already-fired hull-defense missiles may also be present.
    SobGroup_Stop(0, "HWT_Launcher")
    SobGroup_AbilityActivate("HWT_Launcher", AB_Attack, 0)
    SobGroup_TakeDamage("HWT_Primary", 1)
    HWT_Log("target_loss_requested", "method=TakeDamage_1|new_fire=disabled|missiles_in_flight=operator_must_confirm")
    Subtitle_Message("$9984034", 25)
end

function HWT_ScenarioTick()
    HWT_Distance("HWT_Launcher", "HWT_Primary")
    HWT_Distance("HWT_Launcher", "HWT_Replacement")
    if HWT_STARTED == 1 then
        HWT_MissileCount("missile_sample")
        if HWT_KILLED == 1 and Universe_GameTime()-HWT_KILL_TIME >= 35 then HWT_Complete() end
        if HWT_KILLED == 0 and SobGroup_Count("HWT_Primary") == 0 then
            SobGroup_Stop(0, "HWT_Launcher")
            SobGroup_AbilityActivate("HWT_Launcher", AB_Attack, 0)
            HWT_Log("control_invalid", "reason=primary_died_without_operator_trigger")
            HWT_Complete()
            return
        end
        if HWT_KILLED == 0 and Universe_GameTime()-HWT_START >= 45 then
            SobGroup_Stop(0, "HWT_Launcher")
            SobGroup_AbilityActivate("HWT_Launcher", AB_Attack, 0)
            HWT_Log("control_end", "target_loss_requested=0")
            HWT_Complete()
        end
    end
end

function OnInit()
    HWT_Init("missiles", "$9984031", {"HWT_Launcher", "HWT_Primary", "HWT_Replacement"})
    HWT_KILLED = 0
    HWT_SELECTION_READY = 0
    SobGroup_AbilityActivate("HWT_Launcher", AB_Move, 0)
    SobGroup_AbilityActivate("HWT_Primary", AB_Attack, 0)
    SobGroup_AbilityActivate("HWT_Replacement", AB_Attack, 0)
    SobGroup_AbilityActivate("HWT_Primary", AB_Move, 0)
    SobGroup_AbilityActivate("HWT_Replacement", AB_Move, 0)
    HWT_Log("fixture", "shooter_move=0|target_move=0|target_attack=0|new_fire_disabled_at_loss=1|retarget_verdict=manual")
    UI_BindKeyEvent(ONEKEY, "HWT_MissileStart")
    UI_BindKeyEvent(TWOKEY, "HWT_MissileKill")
end
