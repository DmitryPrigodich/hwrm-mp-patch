-- Native callback reuses one group label for many physical hulls.
unit('ds',1,1,1,1);unit('di',1,1,1,1)
groups.sharedDock={'ds'};orders.sharedDock={command=COMMAND_Dock,under=1,actual=0}
local oldRetries=dockRetries
now=30;SobGroup_UnderAttackReissueDock('sharedDock',401)
groups.sharedDock={'di'};orders.sharedDock={command=0,under=1,actual=0}
SobGroup_UnderAttackReissueDock('sharedDock',402)
groups.sharedDock={'ds'};orders.sharedDock={command=COMMAND_Dock,under=1,actual=0}
now=33;SobGroup_UnderAttackReissueDock('sharedDock',401)
assert(dockRetries==oldRetries+1)
now=37;SobGroup_UnderAttackReissueDock('sharedDock',401);assert(dockRetries==oldRetries+1)
now=38;SobGroup_UnderAttackReissueDock('sharedDock',401);assert(dockRetries==oldRetries+2)
orders.sharedDock.command=0;now=40;SobGroup_UnderAttackReissueDock('sharedDock',401)
assert(HWMP_DockStalls[401]==nil and dockRetries==oldRetries+2)
