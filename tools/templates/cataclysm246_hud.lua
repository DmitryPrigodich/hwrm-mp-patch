-- Experimental 2.4.6 owned-fleet gate. No claim of atomic queue reservation.
-- The inaccurate fractional native SU family is disabled in this candidate.
-- Counts include docked squadron entries, not physical surviving hulls.

HWMP_SU246OwnedLocks = HWMP_SU246OwnedLocks or {}
HWMP_SU246State = HWMP_SU246State or {}
HWMP_SU246Policies = {}

function HWMP_SU246PolicyContains(player, key, ship)
    local list = PlayerRace_GetString(player, key, "")
    list = "," .. gsub(strlower(list), "%s", "") .. ","
    return strfind(list, "," .. ship .. ",", 1, 1) ~= nil
end

function HWMP_SU246PolicyRestricted(player, ship)
    if HWMP_SU246PolicyContains(player, "generic_mp_build_restrict", ship) then return 1 end
    if HWMP_SU246PolicyContains(player, "dm_build_restrict", ship) then return 1 end
    if Player_GetLevelOfDifficulty(player) == 0 then
        if HWMP_SU246PolicyContains(player, "generic_sp_build_restrict", ship) then return 1 end
    end
    if GetGameSettingAsNumber("nocruisers") == 1 then
        if HWMP_SU246PolicyContains(player, "dm_nocruisers_build_restrict", ship) then return 1 end
    end
    if GetGameSettingAsNumber("strikecraftgamemode") == 1 then
        if HWMP_SU246PolicyContains(player, "dm_strikecraftgamemode_build_restrict", ship) then return 1 end
    end
    if GetGameSettingAsNumber("carriersonly") > 0 then
        if HWMP_SU246PolicyContains(player, "dm_carriersonly_build_restrict", ship) then return 1 end
    end
    if GetGameSettingAsNumber("research") == 0 then
        if HWMP_SU246PolicyContains(player, "dm_allresearch_build_restrict", ship) then return 1 end
    end
    return 0
end

function HWMP_SU246Snapshot(player)
    local used = 0
    local capacity = 0
    for i = 1, getn(HWMP_SU246Types) do
        local ship = HWMP_SU246Types[i]
        local count = Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping(player, ship)
        used = used + HWMP_CataclysmCosts[ship] * count
        capacity = capacity + (HWMP_SU246Providers[ship] or 0) * count
    end
    if capacity > HWMP_SU246Maximum then capacity = HWMP_SU246Maximum end
    return used, capacity
end

function HWMP_CataclysmUpdateHUD()
    local player = Universe_CurrentPlayer()
    if player < 0 or player >= Universe_PlayerCount() then return end
    local used, capacity = HWMP_SU246Snapshot(player)
    UI_SetTextLabelText("ResourceMenu", "HWMP_SUOwned", used .. "/" .. capacity)
    UI_SetElementVisible("ResourceMenu", "HWMP_SURow", 1)
    return used, capacity
end

function HWMP_SU246Update()
    for player = 0, Universe_PlayerCount() - 1 do
        if Player_IsAlive(player) == 1 then
            local used, capacity = HWMP_SU246Snapshot(player)
            if HWMP_SU246OwnedLocks[player] == nil then HWMP_SU246OwnedLocks[player] = {} end
            local owned = HWMP_SU246OwnedLocks[player]
            if HWMP_SU246Policies[player] == nil then
                local policies = {}
                for i = 1, getn(HWMP_SU246Types) do
                    local ship = HWMP_SU246Types[i]
                    policies[ship] = HWMP_SU246PolicyRestricted(player, ship)
                end
                HWMP_SU246Policies[player] = policies
            end
            for i = 1, getn(HWMP_SU246Types) do
                local ship = HWMP_SU246Types[i]
                local cost = HWMP_CataclysmCosts[ship]
                -- Zero-cost probes retain their native count caps, even over budget.
                local denied = cost > 0 and used + cost > capacity
                local policy = HWMP_SU246Policies[player][ship]
                local restricted = Player_BuildOptionIsRestricted(player, ship)
                if denied and policy == 0 then
                    if restricted == 0 then
                        Player_RestrictBuildOption(player, ship)
                        owned[ship] = 1
                    end
                elseif owned[ship] == 1 then
                    -- Never release a restriction imposed by a known game rule.
                    if policy == 0 and restricted == 1 then
                        Player_UnrestrictBuildOption(player, ship)
                    end
                    owned[ship] = nil
                end
            end
            local previous = HWMP_SU246State[player]
            if previous == nil or previous[1] ~= used or previous[2] ~= capacity then
                print("HWMP_SU246|player=" .. player .. "|used=" .. used .. "|capacity=" .. capacity)
                HWMP_SU246State[player] = {used, capacity}
            end
        end
    end
    HWMP_CataclysmUpdateHUD()
end

function HWMP_CataclysmHUDStart()
    if type(Player_BuildOptionIsRestricted) ~= "function" or
       type(Player_RestrictBuildOption) ~= "function" or
       type(Player_UnrestrictBuildOption) ~= "function" or
       type(Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping) ~= "function" then
        print("HWMP_SU246_ERROR|missing required native build/count API; gate not started")
        return
    end
    print("HWMP SU 2.4.6 test1: owned-fleet gate, queue reservations NOT certified")
    HWMP_SU246Update()
    if Rule_Exists("HWMP_SU246Update") == 0 then
        Rule_AddInterval("HWMP_SU246Update", HWMP_SU246Interval)
    end
end
