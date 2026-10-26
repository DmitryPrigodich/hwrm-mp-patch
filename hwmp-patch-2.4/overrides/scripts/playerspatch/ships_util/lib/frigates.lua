-- allows strike to stay docked with a hyperspacing support frigate
dofilepath("data:scripts/hwmp24/transport.lua")

function DefenseFieldFrigate_Glow(CustomGroup, playerIndex, shipID)
	if (SobGroup_IsDoingAbility(CustomGroup, AB_DefenseField) == 1) then
		FX_PlayEffect("defense-field-active", CustomGroup, 3.5)
	end
end