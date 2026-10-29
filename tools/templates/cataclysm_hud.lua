-- Cataclysm HUD reports nominal owned groups; native supply owns enforcement.
-- No queues, build restrictions or ship ownership are changed by this display.

function HWMP_CataclysmUpdateHUD()
    local player = Universe_CurrentPlayer()
    if player < 0 or player >= Universe_PlayerCount() then return end
    local used = 0
    for ship, cost in HWMP_CataclysmCosts do
        used = used + cost * Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(player, ship)
    end
    local profile = strlower(tostring(GetGameSettingAsString("unitcaps")))
    local limit = HWMP_CataclysmBudgets[profile]
    if limit == nil then limit = "?" end
    UI_SetTextLabelText("ResourceMenu", "HWMP_SUOwned", used .. "/" .. limit)
    UI_SetElementVisible("ResourceMenu", "HWMP_SURow", 1)
    return used
end

function HWMP_CataclysmHUDStart()
    print("HWMP Cataclysm HUD started; unitcaps=" .. tostring(GetGameSettingAsString("unitcaps")))
    if Rule_Exists("HWMP_CataclysmUpdateHUD") == 0 then
        Rule_AddInterval("HWMP_CataclysmUpdateHUD", 1)
    end
end
