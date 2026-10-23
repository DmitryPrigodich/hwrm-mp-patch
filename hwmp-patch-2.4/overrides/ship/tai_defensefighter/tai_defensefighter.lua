defenseFighterMissileTargets = defenseFighterMissileTargets or {}
--
-- Finds and attacks missiles of any player not us.
--
function findAndAttackEnemyMissiles(CustomGroup, playerID, shipID)
    -- get all missiles
    Selection_Create("AllMissiles")
    local numberEnemyMissiles = Selection_GetMissiles("AllMissiles")
    if (numberEnemyMissiles == 0) then return 0 end
    
    -- ... that are close to me
    local defensePoint = SobGroup_GetPosition(CustomGroup)
    local defensePointString = defensePoint[1]..","..defensePoint[2]..","..defensePoint[3]
    Selection_Create("NearMissiles")
    local nearMissiles = Selection_FilterInclude("NearMissiles", "AllMissiles", "NearPoint", defensePointString, ""..4500)
    if (nearMissiles == 0) then return 0 end
    
    -- ... that are not allied missiles
    local playerIndex = 0;
    local playerCount = Universe_PlayerCount();
    while (playerIndex < playerCount) do --  and gameOver
        -- only process 'alive' players
        if (playerIndex ~= playerID and Player_IsAlive(playerIndex) == 1 and AreAllied(playerID, playerIndex) == 1) then
            Selection_FilterExclude("NearMissiles", "NearMissiles", "PlayerOwner", ""..playerIndex, "");
        end
        -- go to next player
        playerIndex = playerIndex+1
    end
    
    -- .. and excludes friendly missiles
    Selection_Create("IncomingMissiles")
    local incomingEnemyMissiles = Selection_FilterExclude("IncomingMissiles", "NearMissiles", "PlayerOwner", ""..playerID, "");
    if (incomingEnemyMissiles == 0) then return 0 end
            

    -- Refresh at the existing 1.25s unit callback cadence. A count is not a target identity.
    defenseFighterMissileTargets[shipID] = incomingEnemyMissiles
    SobGroup_AttackSelection(playerID, CustomGroup, "IncomingMissiles", 1)

    return incomingEnemyMissiles
end

--
-- Update a defense fighter that's guarding someone.
--
function updateDefenseFighterDefense(CustomGroup, playerID, shipID)
    local guard = "DefenseFighterGuardTargets" .. shipID
    local current = "defenseFighterGuardCurrent"
    SobGroup_CreateIfNotExist(guard)
    SobGroup_CreateIfNotExist(current)
    SobGroup_Clear(current)
    SobGroup_GetCommandTargets(current, CustomGroup, COMMAND_Guard)
    if SobGroup_Empty(current) == 0 then SobGroup_Copy(guard, current) end
    findAndAttackEnemyMissiles(CustomGroup, playerID, shipID)
end

function updateDefenseFighterAttack(CustomGroup, playerID, shipID)
    -- Missile selections need not appear in SobGroup_GetCommandTargets.
    if findAndAttackEnemyMissiles(CustomGroup, playerID, shipID) > 0 then return end
    local guard = "DefenseFighterGuardTargets" .. shipID
    SobGroup_CreateIfNotExist(guard)
    if SobGroup_Empty(guard) == 0 then
        SobGroup_GuardSobGroup(CustomGroup, guard)
        SobGroup_Clear(guard)
    end
end

function updateDefenseFighter(CustomGroup, playerID, shipID)

    --print("updateDefenseFighter: shipID "..shipID)

    if (SobGroup_GetCurrentOrder(CustomGroup) == COMMAND_Guard) then
        updateDefenseFighterDefense(CustomGroup, playerID, shipID)
    elseif (SobGroup_GetCurrentOrder(CustomGroup) == COMMAND_Attack) then
        updateDefenseFighterAttack(CustomGroup, playerID, shipID)
    end

end



