-- HWMP Patch 2.4: reversible, owner-scoped temporary ship effects.
-- Group indexes identify squadron entries, never a physical hull count.
if HWMP_EffectRecords == nil then
    HWMP_EffectRecords = { }
end
if HWMP_EffectSerial == nil then
    HWMP_EffectSerial = 0
end
-- Stock save.lua emits string table keys as .key, without bracket quoting.
-- Encode every byte so owner labels remain collision-free Lua identifiers.
function HWMP_OwnerKey(owner)
    local result = "owner"
    for i = 1, strlen(owner) do
        result = result .."_" ..strbyte(owner, i)
    end
    return result
end
function HWMP_Keys(values)
    local result = { }
    local key = next(values, nil)
    while key ~= nil do
        result[getn(result) + 1] = key
        key = next(values, key)
    end
    return result
end
function HWMP_FindEffectRecord(group, create)
    for i = getn(HWMP_EffectRecords), 1, - 1 do
        local record = HWMP_EffectRecords[i]
        if SobGroup_Empty(record.group) == 1 and next(record.abilities, nil) == nil and record.speed == nil then
            tremove(HWMP_EffectRecords, i)
        elseif SobGroup_GroupInGroup(group, record.group) == 1 and SobGroup_GroupInGroup(record.group, group) == 1 then
            return record
        end
    end
    if create ~= 1 then
        return nil
    end
    HWMP_EffectSerial = HWMP_EffectSerial + 1
    local name = "HWMP_EffectTarget_" ..HWMP_EffectSerial
    SobGroup_CreateIfNotExist(name)
    SobGroup_Clear(name)
    SobGroup_SobGroupAdd(name, group)
    local record = { group = name, abilities = { } }
    HWMP_EffectRecords[getn(HWMP_EffectRecords) + 1] = record
    return record
end
function HWMP_BlockRecord(record, owner, abilities, stop_speed)
    owner = HWMP_OwnerKey(owner)
    for i = 1, getn(abilities) do
        local ability = abilities[i]
        local state = record.abilities[ability]
        if state == nil then
            state = { baseline = SobGroup_CanDoAbility(record.group, ability), owners = { } }
            record.abilities[ability] = state
        end
        state.owners[owner] = 1
        SobGroup_AbilityActivate(record.group, ability, 0)
    end
    if stop_speed == 1 then
        if record.speed == nil then
            record.speed = { baseline = SobGroup_GetSpeed(record.group), owners = { } }
        end
        record.speed.owners[owner] = 1
        SobGroup_SetSpeed(record.group, 0)
    end
end
function HWMP_ReleaseRecord(record, owner)
    owner = HWMP_OwnerKey(owner)
    local keys = HWMP_Keys(record.abilities)
    for i = 1, getn(keys) do
        local ability = keys[i]
        local state = record.abilities[ability]
        if state.owners[owner] ~= nil then
            state.owners[owner] = nil
            if next(state.owners, nil) == nil then
                SobGroup_AbilityActivate(record.group, ability, state.baseline)
                record.abilities[ability] = nil
            end
        end
    end
    if record.speed ~= nil and record.speed.owners[owner] ~= nil then
        record.speed.owners[owner] = nil
        if next(record.speed.owners, nil) == nil then
            SobGroup_SetSpeed(record.group, record.speed.baseline)
            record.speed = nil
        end
    end
end
function HWMP_BlockGroup(group, owner, abilities, stop_speed)
    local probe = "HWMP_EffectProbe"
    SobGroup_CreateIfNotExist(probe)
    for i = 0, SobGroup_Count(group) - 1 do
        SobGroup_Clear(probe)
        SobGroup_FillShipsByIndexRange(probe, group, i, 1)
        if SobGroup_Empty(probe) == 0 then
            HWMP_BlockRecord(HWMP_FindEffectRecord(probe, 1), owner, abilities, stop_speed)
        end
    end
end
function HWMP_UnblockGroup(group, owner)
    if getn(HWMP_EffectRecords) == 0 then
        return
    end
    local probe = "HWMP_EffectProbe"
    SobGroup_CreateIfNotExist(probe)
    for i = 0, SobGroup_Count(group) - 1 do
        SobGroup_Clear(probe)
        SobGroup_FillShipsByIndexRange(probe, group, i, 1)
        if SobGroup_Empty(probe) == 0 then
            local record = HWMP_FindEffectRecord(probe, 0)
            if record ~= nil then
                HWMP_ReleaseRecord(record, owner)
            end
        end
    end
end
function HWMP_ReleaseOwner(owner)
    for i = 1, getn(HWMP_EffectRecords) do
        HWMP_ReleaseRecord(HWMP_EffectRecords[i], owner)
    end
end
function HWMP_ReleaseAbility(group, owner, ability)
    owner = HWMP_OwnerKey(owner)
    local probe = "HWMP_EffectProbe"
    SobGroup_CreateIfNotExist(probe)
    for i = 0, SobGroup_Count(group) - 1 do
        SobGroup_Clear(probe)
        SobGroup_FillShipsByIndexRange(probe, group, i, 1)
        if SobGroup_Empty(probe) == 0 then
            local record = HWMP_FindEffectRecord(probe, 0)
            if record ~= nil then
                local state = record.abilities[ability]
                if state ~= nil and state.owners[owner] ~= nil then
                    state.owners[owner] = nil
                    if next(state.owners, nil) == nil then
                        SobGroup_AbilityActivate(record.group, ability, state.baseline)
                        record.abilities[ability] = nil
                    end
                end
            end
        end
    end
end
function HWMP_HasOtherOwner(record, owner)
    owner = HWMP_OwnerKey(owner)
    local prefix = HWMP_OwnerKey("gravwell:")
    local keys = HWMP_Keys(record.abilities)
    for i = 1, getn(keys) do
        local owners = HWMP_Keys(record.abilities[keys[i]].owners)
        for j = 1, getn(owners) do
            if owners[j] ~= owner and strsub(owners[j], 1, strlen(prefix)) == prefix then
                return 1
            end
        end
    end
    return 0
end
function HWMP_ClearReleasedTumble(group, owner)
    local probe = "HWMP_EffectProbe"
    SobGroup_CreateIfNotExist(probe)
    for i = 0, SobGroup_Count(group) - 1 do
        SobGroup_Clear(probe)
        SobGroup_FillShipsByIndexRange(probe, group, i, 1)
        if SobGroup_Empty(probe) == 0 then
            local record = HWMP_FindEffectRecord(probe, 0)
            if record == nil or HWMP_HasOtherOwner(record, owner) == 0 then
                SobGroup_ClearTumble(probe)
            end
        end
    end
end
-- Missions may change their baseline while a temporary effect is active.
-- This is explicit cooperation; the engine API is never globally monkey-patched.
function HWMP_SetAbilityAllowed(group, ability, allowed)
    if getn(HWMP_EffectRecords) == 0 then
        SobGroup_AbilityActivate(group, ability, allowed)
        return
    end
    local probe = "HWMP_EffectProbe"
    SobGroup_CreateIfNotExist(probe)
    for i = 0, SobGroup_Count(group) - 1 do
        SobGroup_Clear(probe)
        SobGroup_FillShipsByIndexRange(probe, group, i, 1)
        if SobGroup_Empty(probe) == 0 then
            local record = HWMP_FindEffectRecord(probe, 0)
            if record ~= nil and record.abilities[ability] ~= nil then
                record.abilities[ability].baseline = allowed
                SobGroup_AbilityActivate(probe, ability, 0)
            else
                SobGroup_AbilityActivate(probe, ability, allowed)
            end
        end
    end
end
function HWMP_SetSpeedAllowed(group, speed)
    if getn(HWMP_EffectRecords) == 0 then
        SobGroup_SetSpeed(group, speed);
        return
    end
    local probe = "HWMP_EffectProbe"
    SobGroup_CreateIfNotExist(probe)
    for i = 0, SobGroup_Count(group) - 1 do
        SobGroup_Clear(probe)
        SobGroup_FillShipsByIndexRange(probe, group, i, 1)
        if SobGroup_Empty(probe) == 0 then
            local record = HWMP_FindEffectRecord(probe, 0)
            if record ~= nil and record.speed ~= nil then
                record.speed.baseline = speed
                SobGroup_SetSpeed(probe, 0)
            else
                SobGroup_SetSpeed(probe, speed)
            end
        end
    end
end
function HWMP_Log(message)
    if HWMP_Debug == 1 then
        print(message)
    end
end
