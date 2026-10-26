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
    HWJ_Sync(0)
    for i = getn(HWMP_EffectRecords), 1, - 1 do
        local record = HWMP_EffectRecords[i]
        if SobGroup_Empty(record.group) == 1 and next(record.abilities, nil) == nil and record.speed == nil then
            tremove(HWMP_EffectRecords, i)
        elseif SobGroup_GroupInGroup(group, record.group) == 1 and SobGroup_GroupInGroup(record.group, group) == 1 then
            HWJ_ReadRecord(record); return record
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
    HWJ_ReadRecord(record); return record
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
    HWJ_MarkOwner(record,owner)
    HWJ_WriteRecord(record)
end
function HWMP_ReleaseRecord(record, owner)
    HWJ_ReadRecord(record)
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
    HWJ_UnmarkOwner(record,owner)
    HWJ_WriteRecord(record)
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
    HWJ_Sync(0)
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
    local marker=HWJ_OwnerName(HWMP_OwnerKey(owner))
    if not HWJ_Exists(marker) or SobGroup_Empty(marker)==1 then return end
    HWJ_Sync(0)
    for i=1,getn(HWMP_EffectRecords) do
        local record=HWMP_EffectRecords[i]
        if HWJ_Exists(record.group) and SobGroup_Empty(record.group)==0 and SobGroup_GroupInGroup(record.group,marker)==1 then
            HWMP_ReleaseRecord(record,owner)
        end
    end
end

function HWMP_ReleaseAbility(group, owner, ability)
    HWJ_Sync(1)
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
    HWJ_Flush()
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
    HWJ_Sync(0)
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
    HWJ_Sync(1)
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
    HWJ_Flush()
end
function HWMP_SetSpeedAllowed(group, speed)
    HWJ_Sync(1)
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
    HWJ_Flush()
end
function HWMP_Log(message)
    if HWMP_Debug == 1 then
        print(message)
    end
end

-- Native checkpoint storage using group membership; no entities or script flags.
function HWJB_Context(name)
    if name == "HWMP_Journal2_Header" then
        return "Global", "HWMP_JC_Root", 1
    end
    local a, b, id, suffix = strfind(name, "^HWMP_Journal2_Record_(%d+)(.*)$")
    assert(id ~= nil)
    return "Record" ..suffix, "HWMP_EffectTarget_" ..id, 0
end
function HWJB_Has(name, anchor, global)
    if not HWJ_Exists(name) or SobGroup_Empty(name) == 1 then
        return 0
    end
    if global == 1 then
        return 1
    end
    if SobGroup_Empty(anchor) == 1 then
        return 0
    end
    return SobGroup_GroupInGroup(anchor, name)
end
function HWJB_Set(name, anchor, global, value)
    if value == 1 then
        SobGroup_CreateIfNotExist(name)
        if global == 1 then
            SobGroup_Clear(name)
        end
        SobGroup_SobGroupAdd(name, anchor)
    elseif HWJ_Exists(name) then
        if global == 1 then
            SobGroup_Clear(name)
        else
            local scratch = "HWMP_JC_Subtract"
            SobGroup_CreateIfNotExist(scratch);
            SobGroup_Clear(scratch)
            SobGroup_FillSubstract(scratch, name, anchor)
            SobGroup_Clear(name);
            SobGroup_SobGroupAdd(name, scratch)
        end
    end
end
function HWJB_NumberWriteWide(prefix, anchor, global, value)
    assert(value == value and abs(value) < 1e100)
    local sign = 0;
    if value < 0 then
        sign = 1;
        value = - value
    end
    local exponent = 0;
    local mantissa = 0
    if value ~= 0 then
        while value >= 2 do
            value = value / 2;
            exponent = exponent + 1
        end
        while value < 1 do
            value = value * 2;
            exponent = exponent - 1
        end
        exponent = exponent + 1023;
        assert(exponent > 0 and exponent < 2047)
        mantissa = (value - 1) * 4503599627370496
        assert(mantissa == floor(mantissa))
    end
    for bit = 1, 52 do
        HWJB_Set(prefix .."_" ..bit, anchor, global, mod(mantissa, 2));
        mantissa = floor(mantissa / 2)
    end
    for bit = 53, 63 do
        HWJB_Set(prefix .."_" ..bit, anchor, global, mod(exponent, 2));
        exponent = floor(exponent / 2)
    end
    HWJB_Set(prefix .."_64", anchor, global, sign)
end
function HWJB_NumberReadWide(prefix, anchor, global)
    local mantissa = 0;
    local exponent = 0;
    local power = 1
    for bit = 1, 52 do
        if HWJB_Has(prefix .."_" ..bit, anchor, global) == 1 then
            mantissa = mantissa + power
        end
        power = power * 2
    end
    power = 1
    for bit = 53, 63 do
        if HWJB_Has(prefix .."_" ..bit, anchor, global) == 1 then
            exponent = exponent + power
        end
        power = power * 2
    end
    assert(exponent < 2047)
    if exponent == 0 then
        assert(mantissa == 0);
        return 0
    end
    local value = (1 + mantissa / 4503599627370496) * 2 ^ (exponent - 1023)
    if HWJB_Has(prefix .."_64", anchor, global) == 1 then
        value = - value
    end
    return value
end
function HWJB_PointWrite(name, point)
    local field, anchor, global = HWJB_Context(name)
    SobGroup_CreateIfNotExist("HWMP_JC_Root")
    if global ~= 1 then
        SobGroup_SobGroupAdd("HWMP_JC_Root", anchor)
    end
    if global == 1 or field == "Record" then
        local flag = name .."_Exists"
        SobGroup_CreateIfNotExist(flag);
        SobGroup_Clear(flag);
        SobGroup_SobGroupAdd(flag, anchor)
    end
    for i = 1, 3 do
        HWJB_NumberWrite("HWMP_JC_" ..field .."_" ..i, anchor, global, point[i])
    end
end
function HWJB_PointRead(name)
    local field, anchor, global = HWJB_Context(name)
    local point = { 0, 0, 0 }
    if not HWJ_Exists(anchor) or SobGroup_Empty(anchor) == 1 then
        return point
    end
    for i = 1, 3 do
        point[i] = HWJB_NumberRead("HWMP_JC_" ..field .."_" ..i, anchor, global)
    end
    return point
end
function HWJC_Write(prefix, anchor, global, value)
    local sign = 0;
    if value < 0 then
        sign = 1;
        value = - value
    end
    local mode = 0;
    local integer = value
    if value ~= floor(value) then
        mode = 1;
        integer = value * 256
    end
    if integer ~= floor(integer) or integer > 9007199254740991 then
        mode = 2
    end
    HWJB_Set(prefix .."_mode1", anchor, global, mod(mode, 2))
    HWJB_Set(prefix .."_mode2", anchor, global, floor(mode / 2))
    if mode == 2 then
        if sign == 1 then
            value = - value
        end
        HWJB_NumberWriteWide(prefix, anchor, global, value);
        return
    end
    local copy = integer;
    local width = 0
    while copy > 0 do
        width = width + 1;
        copy = floor(copy / 2)
    end
    local number = width
    for i = 1, 6 do
        HWJB_Set(prefix .."_width" ..i, anchor, global, mod(number, 2));
        number = floor(number / 2)
    end
    HWJB_Set(prefix .."_sign", anchor, global, sign)
    for i = 1, width do
        HWJB_Set(prefix .."_v" ..i, anchor, global, mod(integer, 2));
        integer = floor(integer / 2)
    end
end
function HWJC_Read(prefix, anchor, global)
    local mode = HWJB_Has(prefix .."_mode1", anchor, global) + 2 * HWJB_Has(prefix .."_mode2", anchor, global)
    if mode == 2 then
        return HWJB_NumberReadWide(prefix, anchor, global)
    end
    assert(mode < 2)
    local width = 0;
    local power = 1
    for i = 1, 6 do
        width = width + power * HWJB_Has(prefix .."_width" ..i, anchor, global);
        power = power * 2
    end
    assert(width <= 53)
    local value = 0;
    power = 1
    for i = 1, width do
        value = value + power * HWJB_Has(prefix .."_v" ..i, anchor, global);
        power = power * 2
    end
    if mode == 1 then
        value = value / 256
    end
    if HWJB_Has(prefix .."_sign", anchor, global) == 1 then
        value = - value
    end
    return value
end
HWJ_OwnerPrefixes = { "gravwell:", "gravwell-self:", "salvage:", "transport:" }
function HWJC_OwnerPush(values, key)
    local raw = HWJ_RawOwner(key)
    for i = 1, getn(HWJ_OwnerPrefixes) do
        local prefix = HWJ_OwnerPrefixes[i]
        if strsub(raw, 1, strlen(prefix)) == prefix then
            local suffix = strsub(raw, strlen(prefix) + 1)
            if strfind(suffix, "^%d+$") and tostring(tonumber(suffix)) == suffix then
                values[getn(values) + 1] = i;
                values[getn(values) + 1] = tonumber(suffix);
                return
            end
        end
    end
    values[getn(values) + 1] = 0
    HWJ_PushOwners(values, { [key] = 1 })
end
function HWJC_OwnerTake(cursor)
    local kind = HWJ_Take(cursor)
    if kind == 0 then
        local owners = HWJ_ReadOwners(cursor);
        local key = next(owners, nil)
        assert(key ~= nil and next(owners, key) == nil);
        return key
    end
    assert(kind >= 1 and kind <= getn(HWJ_OwnerPrefixes))
    return HWMP_OwnerKey(HWJ_OwnerPrefixes[kind] ..HWJ_Take(cursor))
end
function HWJC_Encode(record)
    local keys = HWMP_Keys(record.abilities);
    sort(keys)
    local has_speed = record.speed and 1 or 0
    local values = { 2, getn(keys), has_speed }
    if has_speed == 1 then
        values[getn(values) + 1] = record.speed.baseline
    end
    local all = { }
    for i = 1, getn(keys) do
        local state = record.abilities[keys[i]]
        assert(state.baseline == 0 or state.baseline == 1)
        values[getn(values) + 1] = keys[i] * 2 + state.baseline
        local owners = HWMP_Keys(state.owners)
        for j = 1, getn(owners) do
            all[owners[j]] = 1
        end
    end
    if record.speed then
        local owners = HWMP_Keys(record.speed.owners)
        for j = 1, getn(owners) do
            all[owners[j]] = 1
        end
    end
    local owners = HWMP_Keys(all);
    sort(owners)
    values[getn(values) + 1] = getn(owners)
    local fields = getn(keys) + has_speed
    for i = 1, getn(owners) do
        local owner = owners[i];
        HWJC_OwnerPush(values, owner)
        for first = 1, fields, 24 do
            local mask = 0;
            local power = 1
            for slot = first, min(first + 23, fields) do
                local state = record.speed
                if slot <= getn(keys) then
                    state = record.abilities[keys[slot]]
                end
                if state.owners[owner] then
                    mask = mask + power
                end
                power = power * 2
            end
            values[getn(values) + 1] = mask
        end
    end
    return values
end
function HWJC_Decode(record, values)
    local cursor = { values = values, position = 1 };
    assert(HWJ_Take(cursor) == 2)
    local count = HWJ_Take(cursor);
    local has_speed = HWJ_Take(cursor)
    record.abilities = { };
    record.speed = nil
    if has_speed == 1 then
        record.speed = { baseline = HWJ_Take(cursor), owners = { } }
    end
    local keys = { }
    for i = 1, count do
        local packed = HWJ_Take(cursor);
        local ability = floor(packed / 2)
        keys[i] = ability;
        record.abilities[ability] = { baseline = mod(packed, 2), owners = { } }
    end
    local owners = HWJ_Take(cursor);
    local fields = count + has_speed
    for i = 1, owners do
        local key = HWJC_OwnerTake(cursor)
        for first = 1, fields, 24 do
            local mask = HWJ_Take(cursor);
            assert(mask >= 0 and mask < 16777216)
            for slot = first, min(first + 23, fields) do
                if mod(mask, 2) == 1 then
                    local state = record.speed
                    if slot <= count then
                        state = record.abilities[keys[slot]]
                    end
                    state.owners[key] = 1
                end
                mask = floor(mask / 2)
            end
            assert(mask == 0)
        end
    end
    assert(cursor.position == getn(values) + 1)
end
function HWJB_NumberWrite(prefix, anchor, global, value)
    HWJC_Write(prefix, anchor, global, value)
end
function HWJB_NumberRead(prefix, anchor, global)
    return HWJC_Read(prefix, anchor, global)
end
-- Native checkpoint journal: tables are caches, group membership is checkpoint data.
-- Inline with effects.lua: native file scopes do not support the tested wrapper override.
HWJ_Prefix = "HWMP_Journal2_"
HWJ_Revision = nil
function HWJ_Exists(name)
    local value = SobGroup_Exists(name)
    return value == 1 or value == true
end
function HWJ_PointWrite(name, value)
    HWJB_PointWrite(name, value)
end
function HWJ_Header()
    if HWJ_Exists(HWJ_Prefix .."Header_Exists") then
        return HWJB_PointRead(HWJ_Prefix .."Header")
    end
    return { 0, 0, 0 }
end
function HWJ_RawOwner(key)
    if key == "owner" then
        return ""
    end
    assert(strsub(key, 1, 6) == "owner_")
    local out = ""
    local position = 6
    while position <= strlen(key) do
        local first, last, byte = strfind(key, "_(%d+)", position)
        assert(first == position and byte ~= nil)
        out = out ..strchar(tonumber(byte));
        position = last + 1
    end
    return out
end
function HWJ_PushOwners(values, owners)
    local keys = HWMP_Keys(owners);
    sort(keys)
    values[getn(values) + 1] = getn(keys)
    for i = 1, getn(keys) do
        local raw = HWJ_RawOwner(keys[i]);
        values[getn(values) + 1] = strlen(raw)
        for j = 1, strlen(raw), 3 do
            local packed = 0
            for k = 0, 2 do
                packed = packed * 256
                if j + k <= strlen(raw) then
                    packed = packed + strbyte(raw, j + k)
                end
            end
            values[getn(values) + 1] = packed / 256
        end
    end
end
function HWJ_Take(cursor)
    local value = cursor.values[cursor.position]
    cursor.position = cursor.position + 1;
    assert(value ~= nil);
    return value
end
function HWJ_ReadOwners(cursor)
    local out = { };
    local count = HWJ_Take(cursor);
    assert(count >= 0 and count < 10000)
    for i = 1, count do
        local length = HWJ_Take(cursor);
        assert(length >= 0 and length < 10000)
        local raw = ""
        for j = 1, length, 3 do
            local packed = HWJ_Take(cursor) * 256;
            local bytes = { }
            bytes[1] = floor(packed / 65536);
            bytes[2] = mod(floor(packed / 256), 256);
            bytes[3] = mod(packed, 256)
            for k = 1, 3 do
                if j + k - 1 <= length then
                    raw = raw ..strchar(bytes[k])
                end
            end
        end
        out[HWMP_OwnerKey(raw)] = 1
    end
    return out
end
function HWJ_Encode(record)
    return HWJC_Encode(record)
end
function HWJ_ReadRecord(record)
    if SobGroup_Empty(record.group) == 1 then
        record.abilities = { };
        record.speed = nil;
        return
    end
    local id = tonumber(strsub(record.group, strlen("HWMP_EffectTarget_") + 1))
    assert(id ~= nil)
    local name = HWJ_Prefix .."Record_" ..id
    local marker = name .."_Exists"
    if not HWJ_Exists(marker) or SobGroup_Empty(marker) == 1 or SobGroup_GroupInGroup(record.group, marker) == 0 then
        return
    end
    local header = HWJB_PointRead(name)
    assert(header[2] == 1 and header[1] >= 3 and header[1] < 100000)
    local values = { }
    for i = 1, header[1], 3 do
        local triple = HWJB_PointRead(name .."_" ..i)
        for j = 1, 3 do
            if i + j - 1 <= header[1] then
                values[i + j - 1] = triple[j]
            end
        end
    end
    HWJC_Decode(record, values)
    record.journal_values = values
end
function HWJ_Sync(force)
    local header = HWJ_Header()
    if force == 1 or HWJ_Revision ~= header[2] or HWMP_EffectSerial ~= header[1] then
        if HWMP_Debug == 1 then
            print("HWMP_JOURNAL|event=sync|t=" ..Universe_GameTime() .."|native_revision=" ..header[2] .."|cached_revision=" ..(HWJ_Revision or - 1) .."|serial=" ..header[1])
        end
        HWMP_EffectRecords = { };
        HWMP_EffectSerial = header[1]
        for id = 1, header[1] do
            local group = "HWMP_EffectTarget_" ..id
            if HWJ_Exists(group) then
                local record = { group = group, abilities = { } }
                HWJ_ReadRecord(record)
                HWMP_EffectRecords[getn(HWMP_EffectRecords) + 1] = record
            end
        end
    else
        -- A different checkpoint branch can have the same counter values.
        -- Restore native registry entries that a previous branch pruned from its cache.
        local known = { }
        for i = 1, getn(HWMP_EffectRecords) do
            known[HWMP_EffectRecords[i].group] = 1
        end
        for id = 1, header[1] do
            local group = "HWMP_EffectTarget_" ..id
            if known[group] == nil and HWJ_Exists(group) and SobGroup_Empty(group) == 0 then
                local record = { group = group, abilities = { } }
                HWJ_ReadRecord(record);
                HWMP_EffectRecords[getn(HWMP_EffectRecords) + 1] = record
            end
        end
    end
    HWJ_Revision = header[2]
end
function HWJ_WriteRecord(record)
    local values = HWJ_Encode(record);
    local old = record.journal_values
    local same = old and getn(old) == getn(values)
    if same then
        for i = 1, getn(values) do
            if old[i] ~= values[i] then
                same = nil;
                break
            end
        end
    end
    if same then
        return
    end
    local id = tonumber(strsub(record.group, strlen("HWMP_EffectTarget_") + 1))
    local name = HWJ_Prefix .."Record_" ..id
    for i = 1, getn(values), 3 do
        HWJ_PointWrite(name .."_" ..i, { values[i], values[i + 1] or 0, values[i + 2] or 0 })
    end
    HWJ_PointWrite(name, { getn(values), 1, 0 })
    local header = HWJ_Header()
    HWJ_Revision = mod(header[2], 65534) + 1
    if HWMP_Debug == 1 then
        print("HWMP_JOURNAL|event=commit|t=" ..Universe_GameTime() .."|record=" ..id .."|revision=" ..HWJ_Revision .."|speed=" ..(record.speed and record.speed.baseline or - 1))
    end
    HWJ_PointWrite(HWJ_Prefix .."Header", { HWMP_EffectSerial, HWJ_Revision, 1 })
    record.journal_values = values
end
function HWJ_OwnerName(key)
    local raw = HWJ_RawOwner(key);
    local name = "HWMP_J2_O"
    for i = 1, strlen(raw) do
        name = name .."_" ..format("%02x", strbyte(raw, i))
    end
    return name
end
function HWJ_OwnerHas(owner, group)
    local name = HWJ_OwnerName(HWMP_OwnerKey(owner))
    if not HWJ_Exists(name) or SobGroup_Empty(name) == 1 then
        return 0
    end
    if group == nil then
        return 1
    end
    if SobGroup_Empty(group) == 1 then
        return 0
    end
    return SobGroup_GroupInGroup(group, name)
end
function HWJ_MarkOwner(record, key)
    local name = HWJ_OwnerName(key);
    SobGroup_CreateIfNotExist(name);
    SobGroup_SobGroupAdd(name, record.group)
end
function HWJ_UnmarkOwner(record, key)
    local abilities = HWMP_Keys(record.abilities)
    for i = 1, getn(abilities) do
        if record.abilities[abilities[i]].owners[key] then
            return
        end
    end
    if record.speed and record.speed.owners[key] then
        return
    end
    local name = HWJ_OwnerName(key)
    if HWJ_Exists(name) then
        local scratch = "HWMP_J2_OwnerSubtract";
        SobGroup_CreateIfNotExist(scratch);
        SobGroup_Clear(scratch)
        SobGroup_FillSubstract(scratch, name, record.group);
        SobGroup_Clear(name);
        SobGroup_SobGroupAdd(name, scratch)
    end
end
function HWJ_PreviousGroup(id)
    local name = "gravwell-" ..id .."-previously-stunned"
    SobGroup_CreateIfNotExist(name)
    if HWJ_OwnerHas("gravwell:" ..id) == 0 then
        SobGroup_Clear(name)
    end
    return name
end


function HWJ_Flush()
 for i=1,getn(HWMP_EffectRecords) do HWJ_WriteRecord(HWMP_EffectRecords[i]) end
end
