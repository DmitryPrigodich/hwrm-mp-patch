-- allows strike to stay docked with a hyperspacing support frigate
function SupportFrigate_HyperspaceDock(CustomGroup, shipID)
    local owner = "transport:" .. shipID
	if (SobGroup_AreAllInRealSpace(CustomGroup)==1) then
		if (SobGroup_Empty("LatchDockTempGroup"..shipID)==0) then --Exited Hyperspace with ships docked
			if (SobGroup_IsDoingAbility("LatchDockTempGroup"..shipID, AB_Dock) == 0) then
				HWMP_ReleaseAbility("LatchDockTempGroup"..shipID, owner, AB_Dock)
				SobGroup_DockSobGroupAndStayDocked("LatchDockTempGroup"..shipID, CustomGroup)
			end
			SobGroup_Clear("LatchDockTempGroup")
			SobGroup_GetSobGroupDockedWithGroup(CustomGroup, "LatchDockTempGroup")
			if (SobGroup_Count("LatchDockTempGroup") >= SobGroup_Count("LatchDockTempGroup"..shipID)) then --All ships docked
				if (SobGroup_Empty("LatchDockTempGroup"..shipID) == 0) then
					SobGroup_MakeSelectable("LatchDockTempGroup"..shipID, 1)
					SobGroup_SetHidden("LatchDockTempGroup"..shipID, 0)
					HWMP_ReleaseOwner(owner)
					SobGroup_Clear("LatchDockTempGroup"..shipID)
				end
			end
		elseif (SobGroup_GetROE(CustomGroup)==0) then --In Offensive ROE, launch all ships
			SobGroup_Clear("LatchDockTempGroup")
			SobGroup_GetSobGroupDockedWithGroup(CustomGroup, "LatchDockTempGroup")
			SobGroup_Launch("LatchDockTempGroup", CustomGroup)
		elseif (SobGroup_GetROE(CustomGroup)==2) then --In Passive ROE, all ships stay docked
			SobGroup_GetSobGroupDockedWithGroup(CustomGroup, "LatchDockTempGroup")
			SobGroup_ForceStayDockedIfDocking("LatchDockTempGroup")
			SobGroup_Clear("LatchDockTempGroup")
		end
	elseif (SobGroup_Empty("LatchDockTempGroup"..shipID) == 1) then --Hyperspacing, get all ships docked with
		SobGroup_GetSobGroupDockedWithGroup(CustomGroup, "LatchDockTempGroup"..shipID)
		SobGroup_AbilityActivate(CustomGroup, AB_Lights, 0)
		SobGroup_MakeSelectable("LatchDockTempGroup"..shipID, 0)
		SobGroup_SetHidden("LatchDockTempGroup"..shipID, 1)
		HWMP_BlockGroup("LatchDockTempGroup"..shipID, owner, { AB_Dock, AB_Scuttle, AB_Attack }, 0)
	else --Hyperspacing with ships docked
		if (SobGroup_AreAllInHyperspace("LatchDockTempGroup"..shipID)==0)and(SobGroup_CanDoAbility(CustomGroup,AB_Lights)==0) then --Entering Hyperspace
			SobGroup_Despawn("LatchDockTempGroup"..shipID)
		elseif (SobGroup_AreAllInHyperspace("LatchDockTempGroup"..shipID)==1)and(SobGroup_AreAllInHyperspace(CustomGroup)==1) then --All In Hyperspace
			SobGroup_AbilityActivate(CustomGroup, AB_Lights, 1)
		elseif (SobGroup_AreAllInHyperspace(CustomGroup)==0)and(SobGroup_CanDoAbility(CustomGroup,AB_Lights)==1) then --Exiting Hyperspace
			Volume_AddSphere("LatchDockTempVolume", SobGroup_GetPosition(CustomGroup), 0)
			SobGroup_Spawn("LatchDockTempGroup"..shipID, "LatchDockTempVolume")
			Volume_Delete("LatchDockTempVolume")
		end
	end
end

-- hgn def field glow
function DefenseFieldFrigate_Glow(CustomGroup, playerIndex, shipID)
	if (SobGroup_IsDoingAbility(CustomGroup, AB_DefenseField) == 1) then
		FX_PlayEffect("defense-field-active", CustomGroup, 3.5)
	end
end