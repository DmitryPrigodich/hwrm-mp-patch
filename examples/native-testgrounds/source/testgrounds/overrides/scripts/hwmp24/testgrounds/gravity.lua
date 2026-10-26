dofilepath("data:scripts/SCAR/SCAR_Util.lua")
dofilepath("data:scripts/hwmp24/testgrounds/version.lua")
dofilepath("data:scripts/hwmp24/testgrounds/common.lua")

function HWT_GravityMarker()
    HWT_MARKER = HWT_MARKER + 1
    HWT_Log("manual_marker", "index=" .. HWT_MARKER .. "|note=operator_observation")
    Subtitle_Message("$9984013", 15)
end

function HWT_GravityDestroy()
    if SobGroup_Count("HWT_KusB") > 0 then
        HWT_Log("destroy_requested", "group=HWT_KusB|method=TakeDamage_1")
        SobGroup_TakeDamage("HWT_KusB", 1)
    end
    if SobGroup_Count("HWT_TaiB") > 0 then
        HWT_Log("destroy_requested", "group=HWT_TaiB|method=TakeDamage_1")
        SobGroup_TakeDamage("HWT_TaiB", 1)
    end
end

function HWT_ScenarioTick()
    HWT_Distance("HWT_KusA", "HWT_KusFriendly")
    HWT_Distance("HWT_KusB", "HWT_KusFriendly")
    HWT_Distance("HWT_TaiA", "HWT_TaiFriendly")
    HWT_Distance("HWT_TaiB", "HWT_TaiFriendly")
    -- No direct GW_MEM/effect calls: only the ship's real custom callbacks may act.
end

function OnInit()
    HWT_Init("gravity", "$9984011", {
        "HWT_KusA", "HWT_KusB", "HWT_TaiA", "HWT_TaiB",
        "HWT_KusFriendly", "HWT_KusEnemy", "HWT_TaiFriendly", "HWT_TaiEnemy"
    })
    HWT_MARKER = 0
    -- Deliberate pre-existing restriction: its zero baseline must be preserved.
    SobGroup_AbilityActivate("HWT_KusEnemy", AB_Attack, 0)
    SobGroup_AbilityActivate("HWT_TaiEnemy", AB_Attack, 0)
    HWT_Log("fixture", "enemy_attack_baseline=0|friendly_attack_baseline=unmodified|radius=3000|activation=human_native_button")
    UI_BindKeyEvent(ONEKEY, "HWT_GravityMarker")
    UI_BindKeyEvent(TWOKEY, "HWT_GravityDestroy")
end
