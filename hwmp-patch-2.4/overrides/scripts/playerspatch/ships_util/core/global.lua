dofilepath("data:scripts/hwmp24/effects.lua")
-- global.lua
-- For any functionality which isn't ship/race specific
-- By: Fear, QuadS

-- Creates a new sobgroup if one doesn't exist, then clears the group to ensure
-- the group referenced by the return string is clear.
function SobGroup_CreateAndClear(name)
	SobGroup_CreateIfNotExist(name)
	SobGroup_Clear(name)
	return name;
end

-- overwrites target_group with the content of incoming_group
function SobGroup_Overwrite(target_group, incoming_group)
	SobGroup_Clear(target_group)
	SobGroup_SobGroupAdd(target_group, incoming_group)
end


--- Creates a new sobgroup if one doesn't exist, then clears the group to ensure the group referenced by the return string is clear.
---@param group_name string
---@return string
function SobGroup_Fresh(group_name)
	SobGroup_CreateIfNotExist(group_name);
	SobGroup_Clear(group_name);
	return group_name;
end

--- Creates a new SobGroup, named with `new_name`, or '<original-name>-clone', if a new name is not provided for the group.
---@param original string
---@param new_name? string
---@return string
function SobGroup_Clone(original, new_name)
	new_name = new_name or (original .. "-clone");
	SobGroup_Fresh(new_name);
	SobGroup_SobGroupAdd(new_name, original);
	return new_name;
end

--- _Splits_ a given `group` into a table of subgroups. The size of the subgroups is given by `granularity`.
---
---@param group string
---@param granularity? integer
---@return string[]
function SobGroup_Split(group, granularity)
    granularity = granularity or 1
    if granularity < 1 then granularity = 1 end
    local result = {}
    for i = 0, SobGroup_Count(group) - 1, granularity do
        local subgroup = SobGroup_Fresh(group .. "-subgroup-" .. i)
        SobGroup_FillShipsByIndexRange(subgroup, group, i, granularity)
        if SobGroup_Empty(subgroup) == 0 then result[getn(result) + 1] = subgroup end
    end
    return result
end

function SobGroup_NoSalvageScuttle(group)
    local owner = "salvage:" .. group
    if SobGroup_IsDoingAbility(group, AB_Dock) == 1 then
        HWMP_BlockGroup(group, owner, { AB_Scuttle }, 0)
    else HWMP_ReleaseOwner(owner) end
end

HWMP_DockStalls = HWMP_DockStalls or {}
function SobGroup_UnderAttackReissueDock(group)
    if SobGroup_GetCurrentOrder(group) ~= COMMAND_Dock or SobGroup_IsDocked(group) == 1 or
       SobGroup_UnderAttack(group) ~= 1 or SobGroup_CanDoAbility(group, AB_Dock) ~= 1 or
       SobGroup_CanDoAbility(group, AB_Move) ~= 1 then
        HWMP_DockStalls[group] = nil
        return
    end
    local now = Universe_GameTime()
    if SobGroup_GetActualSpeed(group) >= 1 then HWMP_DockStalls[group] = nil; return end
    local state = HWMP_DockStalls[group]
    if state == nil then state = { since = now, retry = -100 }; HWMP_DockStalls[group] = state end
    if now - state.since >= 3 and now - state.retry >= 5 then
        SobGroup_DockSobGroupWithAny(group)
        state.retry = now
        state.since = now
    end
end

function SobGroup_AnyBeingCaptured(group)
	local group_being_captured = group .. "_being_captured"
	SobGroup_CreateAndClear(group_being_captured)
	SobGroup_GetSobGroupBeingCapturedGroup(group, group_being_captured)
	if (SobGroup_Count(group_being_captured) > 0) then
		return 1
	end
	return 0
end

-- Checks to see if any ship in `group` has attack targets
function SobGroup_AnyAreAttacking(group)
	local group_attacking = group .. "_attacking"
	SobGroup_CreateAndClear(group_attacking)
	SobGroup_GetCommandTargets(group_attacking, group, COMMAND_Attack)
	if (SobGroup_Count(group_attacking) > 0) then
		return 1
	end
	return 0
end

-- returns a group of all active ships for all players
function Universe_GetAllActiveShips(target_group)
	local all_ships = "all-ships"
	SobGroup_CreateIfNotExist(all_ships)
	SobGroup_Clear(all_ships)
	for i = 0, Universe_PlayerCount() - 1 do
		if (Player_IsAlive(i) == 1) then
			SobGroup_SobGroupAdd(all_ships, "Player_Ships" .. i)
		end
	end
	if (target_group ~= nil) then
		SobGroup_CreateIfNotExist(target_group)
		SobGroup_Clear(target_group)
		SobGroup_SobGroupAdd(target_group, all_ships)
		return target_group
	end
	return all_ships
end

-- multiplies the ship's max-speed multiplier by 'mult'
function SobGroup_AlterSpeedMult(target_group, mult)
	if (mult == nil) then
		mult = 1/2
	end
	local speed_mult = SobGroup_GetSpeed(target_group) * mult
	if (speed_mult < 0.05) then
		speed_mult = 0
	end
	SobGroup_SetSpeed(target_group, speed_mult)

	return target_group
end

STUN_EFFECT_ABILITIES = {
	-- AB_Cloak,
	-- AB_AcceptDocking,
	-- AB_Builder,
	-- AB_Hyperspace,
	-- AB_FormHyperspaceGate,
	-- AB_HyperspaceViaGate,
	AB_SpecialAttack,
	-- AB_DefenseField,
	-- AB_DefenseFieldShield,
	AB_Steering,
	AB_Targeting,
	-- AB_Lights,
}
STUN_EFFECT_EVENT = "PowerOff"

-- sets whether the given group should be 'stunned' or not (AB_Move/AB_Steering/AB_Attack/AB_Targeting)
function SobGroup_SetGroupStunned(target_group, stunned, duration)
	if (duration == nil) then
		duration = 99
	end
	if (SobGroup_Count(target_group) > 0) then
		if (stunned == 1) then
			FX_StartEvent(target_group, STUN_EFFECT_EVENT)
			SobGroup_Disable(target_group, duration)
			SobGroup_SetSpeed(target_group, 0)
		else
			FX_StopEvent(target_group, STUN_EFFECT_EVENT)
			SobGroup_Disable(target_group, 0)
			SobGroup_SetSpeed(target_group, 1)
		end
		local ability_status = modulo(stunned + 1, 2) -- 0 -> 1, 1 -> 0, 2 -> 1, ...
		for _, ability in STUN_EFFECT_ABILITIES do
			SobGroup_AbilityActivate(target_group, ability, ability_status)
		end
	end
	return target_group
end

DEFAULT_SOBGROUP = SobGroup_CreateAndClear("__PLAYERSPATCH_EMPTY_GROUP")
