-- Native turns Scuttle off before our first towing callback. Two hulls share callback name.
local rawCanDoAbility=SobGroup_CanDoAbility
function SobGroup_CanDoAbility(g,ability)
 if ability==AB_Scuttle and SobGroup_IsDoingAbility(g,AB_Dock)==1 then return 0 end
 return rawCanDoAbility(g,ability)
end
unit('s1',1,1,1,1);unit('s0',1,1,0,1)
groups.shared={'s1'};orders.shared={}
SobGroup_NoSalvageScuttle('shared',0,201)
groups.shared={'s0'};SobGroup_NoSalvageScuttle('shared',0,202)
ships.s1.a[AB_Scuttle]=0;groups.shared={'s1'};orders.shared={[AB_Dock]=1}
SobGroup_NoSalvageScuttle('shared',0,201)
assert(ships.s1.a[AB_Scuttle]==0)
groups.shared={'s0'};orders.shared={};SobGroup_NoSalvageScuttle('shared',0,202)
assert(ships.s1.a[AB_Scuttle]==0) -- Idle hull must not release the other hull's owner.
groups.shared={'s1'};orders.shared={};SobGroup_NoSalvageScuttle('shared',0,201)
assert(ships.s1.a[AB_Scuttle]==1 and ships.s0.a[AB_Scuttle]==0)
-- A different effect and a cooperative permanent prohibition survive release.
orders.shared={[AB_Dock]=1};ships.s1.a[AB_Scuttle]=0
SobGroup_NoSalvageScuttle('shared',0,201)
HWMP_BlockGroup('shared','transport:other',{AB_Scuttle},0)
HWMP_SetAbilityAllowed('shared',AB_Scuttle,0)
orders.shared={};SobGroup_NoSalvageScuttle('shared',0,201)
HWMP_ReleaseOwner('transport:other');assert(ships.s1.a[AB_Scuttle]==0)
-- Native ownership transfer loses old group membership, keeps the supplied hull ID.
unit('oldCapture',1,1,1,1);groups.transferred={'oldCapture'};orders.transferred={}
SobGroup_NoSalvageScuttle('transferred',0,203)
ships.oldCapture.a[AB_Scuttle]=0;orders.transferred={[AB_Dock]=1}
SobGroup_NoSalvageScuttle('transferred',0,203)
for _,r in ipairs(HWMP_EffectRecords) do
 if groups[r.group][1]=='oldCapture' then groups[r.group]={} end
end
unit('newCapture',1,1,0,1);groups.transferred={'newCapture'};orders.transferred={}
SobGroup_NoSalvageScuttle('transferred',4,203)
assert(ships.newCapture.a[AB_Scuttle]==1)
