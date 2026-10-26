-- Contract regression: a redocking stall must not retain transport locks/visibility.
unit('carrier',1,1,1,1);unit('a',1,0,0,0.75);unit('b',1,1,1,1.25)
groups.carrier={'carrier'};groups.cargo={'a','b'};groups.LatchDockTempGroup={}
spawnCount=0;dockCount=0;stopCount=0;volumes={};deferSpawn=false;pendingSpawns={}
function finishSpawns() for _,id in ipairs(pendingSpawns) do ships[id].real=1 end;pendingSpawns={} end
function SobGroup_AreAllInRealSpace(g)
 for _,id in ipairs(groups[g] or {}) do if ships[id].real~=1 then return 0 end end
 return 1
end
function SobGroup_AreAllInHyperspace(g)
 for _,id in ipairs(groups[g] or {}) do if ships[id].real==1 then return 0 end end
 return 1
end
function SobGroup_GetPosition(g) return {100,0,200} end
function SobGroup_GetPlayerOwner(g) return 0 end
function SobGroup_GetSobGroupDockedWithGroup(g,dst)
 groups[dst]={}
 for _,id in ipairs(groups.cargo) do if ships[id].real==1 and ships[id].docked==1 then table.insert(groups[dst],id) end end
end
function SobGroup_MakeSelectable(g,n) for _,id in ipairs(groups[g] or {}) do ships[id].selectable=n end end
function SobGroup_SetHidden(g,n) for _,id in ipairs(groups[g] or {}) do ships[id].hidden=n end end
function SobGroup_GetROE(g) return 1 end
function SobGroup_Despawn(g) for _,id in ipairs(groups[g]) do ships[id].real=0 end end
function Volume_AddSphere(name,position,radius) volumes[name]=position end
function Volume_Delete(name) volumes[name]=nil end
function SobGroup_Spawn(g,volume)
 assert(volumes[volume]~=nil)
 for _,id in ipairs(groups[g]) do if deferSpawn then table.insert(pendingSpawns,id) else ships[id].real=1 end;ships[id].docked=0;spawnCount=spawnCount+1 end
end
function SobGroup_Stop(owner,g) stopCount=stopCount+1 end
function SobGroup_DockSobGroupAndStayDocked(g,carrier)
 dockCount=dockCount+1 -- Intentionally never finishes: this is the failure being guarded.
end
ships.carrier.real=1;ships.a.real=1;ships.b.real=1;ships.a.docked=1;ships.b.docked=1
HWMP_TransportRemember('carrier',50)
ships.carrier.real=0
SupportFrigate_HyperspaceDock('carrier',50)
assert(ships.b.a[AB_Attack]==0 and ships.b.a[AB_Dock]==0 and ships.b.hidden==1)
HWMP_SetAbilityAllowed('cargo',AB_Scuttle,0)
HWMP_BlockGroup('cargo','gravwell:10',{AB_Attack},1)
SupportFrigate_HyperspaceDock('carrier',50) -- Native descent/despawn phase.
assert(ships.a.real==0 and ships.b.real==0)
ships.carrier.real=1
SupportFrigate_HyperspaceDock('carrier',50)
assert(spawnCount==2 and stopCount==2 and dockCount==2)
assert(ships.a.real==1 and ships.b.real==1 and ships.a.hidden==0 and ships.b.hidden==0)
assert(ships.a.selectable==1 and ships.b.selectable==1 and SobGroup_Count('LatchDockTempGroup50')==0)
assert(ships.a.a[AB_Dock]==1 and ships.b.a[AB_Attack]==0 and ships.b.a[AB_Scuttle]==0)
HWMP_ReleaseOwner('gravwell:10')
assert(ships.a.a[AB_Attack]==0 and ships.b.a[AB_Attack]==1 and ships.a.speed==0.75 and ships.b.speed==1.25)
