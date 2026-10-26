-- Transport locks cover hyperspace only; redocking must never keep ships hidden.
if HWMP_TransportAnchors == nil then HWMP_TransportAnchors = {} end

function HWMP_TransportRemember(group, ship_id)
    local own = "HWMP_TransportCarrier_" .. ship_id
    SobGroup_CreateIfNotExist(own)
    if own ~= group then
        SobGroup_Clear(own)
        SobGroup_SobGroupAdd(own, group)
    end
    if SobGroup_Empty(own) == 0 and SobGroup_AreAllInRealSpace(own) == 1 then
        HWMP_TransportAnchors[ship_id] = SobGroup_GetPosition(own)
    end
    return own
end

function HWMP_TransportReturn(carrier, ship_id, position, redock)
    local payload = "LatchDockTempGroup" .. ship_id
    SobGroup_CreateIfNotExist(payload)
    if SobGroup_Empty(payload) == 1 then return 1 end
    local parts = SobGroup_Split(payload)
    for i = 1, getn(parts) do
        local part = parts[i]
        if SobGroup_AreAllInRealSpace(part) == 0 then
            if position == nil then return 0 end
            local volume = "HWMP_TransportReturn_" .. ship_id .. "_" .. i
            -- Keep returning craft clear of the frigate hull and of one another.
            Volume_AddSphere(volume, { position[1] + 500 + i * 250, position[2], position[3] + 500 }, 0)
            SobGroup_Spawn(part, volume)
            Volume_Delete(volume)
        end
    end
    -- Destroy runs once; Spawn enters real space after this callback returns.
    if redock == 1 and SobGroup_AreAllInRealSpace(payload) == 0 then return 0 end
    HWMP_ReleaseOwner("transport:" .. ship_id)
    SobGroup_MakeSelectable(payload, 1)
    SobGroup_SetHidden(payload, 0)
    if redock == 1 then
        local docked = "HWMP_TransportDocked_" .. ship_id
        SobGroup_CreateIfNotExist(docked)
        SobGroup_Clear(docked)
        SobGroup_GetSobGroupDockedWithGroup(carrier, docked)
        for i = 1, getn(parts) do
            local part = parts[i]
            if SobGroup_GroupInGroup(part, docked) == 0 and SobGroup_CanDoAbility(part, AB_Dock) == 1 then
                -- Replace stale pre-jump Dock once. Subsequent player orders win.
                SobGroup_Stop(SobGroup_GetPlayerOwner(part), part)
                SobGroup_DockSobGroupAndStayDocked(part, carrier)
            end
        end
    end
    SobGroup_Clear(payload)
    return 1
end

function SupportFrigate_HyperspaceDock(group, ship_id)
    local carrier = HWMP_TransportRemember(group, ship_id)
    local payload = "LatchDockTempGroup" .. ship_id
    SobGroup_CreateIfNotExist(payload)
    local scratch = "HWMP_TransportAttached_" .. ship_id
    SobGroup_CreateIfNotExist(scratch)
    if SobGroup_AreAllInRealSpace(carrier) == 1 then
        if SobGroup_Empty(payload) == 0 then
            HWMP_TransportReturn(carrier, ship_id, HWMP_TransportAnchors[ship_id], 1)
        elseif SobGroup_GetROE(carrier) == 0 then
            SobGroup_Clear(scratch)
            SobGroup_GetSobGroupDockedWithGroup(carrier, scratch)
            SobGroup_Launch(scratch, carrier)
        elseif SobGroup_GetROE(carrier) == 2 then
            SobGroup_Clear(scratch)
            SobGroup_GetSobGroupDockedWithGroup(carrier, scratch)
            SobGroup_ForceStayDockedIfDocking(scratch)
        end
    elseif SobGroup_Empty(payload) == 1 then
        SobGroup_GetSobGroupDockedWithGroup(carrier, payload)
        SobGroup_AbilityActivate(carrier, AB_Lights, 0)
        SobGroup_MakeSelectable(payload, 0)
        SobGroup_SetHidden(payload, 1)
        HWMP_BlockGroup(payload, "transport:" .. ship_id, { AB_Dock, AB_Scuttle, AB_Attack }, 0)
    elseif SobGroup_AreAllInHyperspace(payload) == 0 and SobGroup_CanDoAbility(carrier, AB_Lights) == 0 then
        SobGroup_Despawn(payload)
    elseif SobGroup_AreAllInHyperspace(payload) == 1 and SobGroup_AreAllInHyperspace(carrier) == 1 then
        SobGroup_AbilityActivate(carrier, AB_Lights, 1)
    end
end

function HWMP_TransportDestroy(group, ship_id)
    local carrier = "HWMP_TransportCarrier_" .. ship_id
    SobGroup_CreateIfNotExist(carrier)
    HWMP_TransportReturn(carrier, ship_id, HWMP_TransportAnchors[ship_id], 0)
    HWMP_TransportAnchors[ship_id] = nil
    SobGroup_Clear(carrier)
end
