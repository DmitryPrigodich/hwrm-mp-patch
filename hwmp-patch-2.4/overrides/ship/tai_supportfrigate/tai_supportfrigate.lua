function Create_Tai_SupportFrigate(CustomGroup, playerIndex, shipID)
    HWMP_TransportRemember(CustomGroup, shipID)
	SobGroup_Create("LatchDockTempGroup"..shipID)
	SobGroup_CreateIfNotExist("LatchDockTempGroup")
end

function Update_Tai_SupportFrigate(CustomGroup, playerIndex, shipID)
	SobGroup_NoSalvageScuttle(CustomGroup, playerIndex, shipID)
	SupportFrigate_HyperspaceDock(CustomGroup, shipID)
end

function Destroy_Tai_SupportFrigate(CustomGroup, playerIndex, shipID)
    HWMP_TransportDestroy(CustomGroup, shipID)
end

