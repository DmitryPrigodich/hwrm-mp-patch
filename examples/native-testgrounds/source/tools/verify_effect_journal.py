"""World rollback regressions. Lua 5.1 mocks do not prove native save/load."""

import json


def verify(vm_factory=None):
    if vm_factory is None:
        from verify_hwmp24 import vm_for

        vm_factory = vm_for
    vm, _ = vm_factory()
    vm.execute("""
function copy_native(value)
 if type(value)~='table' then return value end
 local out={};for k,v in pairs(value) do out[k]=copy_native(v) end;return out
end
unit('x',0,1,0,0.65);unit('y',1,0,1,1.25)
groups.x={'x'};groups.y={'y'};groups.all={'x','y'}
HWMP_BlockGroup('all','gravwell:1',{AB_Move,AB_Attack},1)
HWMP_BlockGroup('y','gravwell:2',{AB_Move,AB_Attack},1)
HWMP_BlockGroup('x','transport:1',{AB_Attack,AB_Scuttle},0)
local saved={groups=copy_native(groups),ships=copy_native(ships)}
HWMP_ReleaseOwner('gravwell:1');HWMP_ReleaseOwner('gravwell:2');HWMP_ReleaseOwner('transport:1')
groups=copy_native(saved.groups);ships=copy_native(saved.ships)
HWMP_ReleaseOwner('gravwell:1')
assert(ships.x.a[AB_Move]==0 and ships.x.a[AB_Attack]==0 and ships.x.speed==0.65)
assert(ships.y.a[AB_Move]==0 and ships.y.speed==0)
HWMP_ReleaseOwner('gravwell:2');HWMP_ReleaseOwner('transport:1')
assert(ships.x.a[AB_Attack]==1 and ships.x.a[AB_Scuttle]==0)
assert(ships.y.a[AB_Move]==1 and ships.y.a[AB_Attack]==0 and ships.y.speed==1.25)
groups=copy_native(saved.groups);ships=copy_native(saved.ships)
HWMP_EffectRecords={};HWMP_EffectSerial=0;HWJ_Revision=nil
HWMP_ReleaseOwner('gravwell:2');HWMP_ReleaseOwner('gravwell:1');HWMP_ReleaseOwner('transport:1')
assert(ships.x.a[AB_Move]==0 and ships.x.a[AB_Attack]==1 and ships.x.speed==0.65)
assert(ships.y.a[AB_Move]==1 and ships.y.a[AB_Attack]==0 and ships.y.speed==1.25)
HWMP_BlockGroup('y','gravwell:3',{AB_Move},1)
HWMP_SetAbilityAllowed('y',AB_Move,0);HWMP_SetSpeedAllowed('y',0.8)
HWMP_EffectRecords={};HWMP_EffectSerial=0;HWJ_Revision=nil
HWMP_ReleaseOwner('gravwell:3');assert(ships.y.a[AB_Move]==0 and ships.y.speed==0.8)
-- A cache hole at an unchanged native revision must not lose a saved target.
HWMP_BlockGroup('x','gravwell:4',{AB_Attack},1)
HWMP_EffectRecords={}
HWMP_ReleaseOwner('gravwell:4')
assert(ships.x.a[AB_Attack]==1 and ships.x.speed==0.65)
-- More than 24 fields, numeric/full-width speeds and arbitrary owner labels.
local abilities={}
for i=20,50 do abilities[getn(abilities)+1]=i;ships.x.a[i]=mod(i,2) end
local owner='custom owner: [] / a_b'
HWMP_BlockGroup('x',owner,abilities,1)
HWMP_BlockGroup('x','gravwell:500',abilities,1)
HWMP_EffectRecords={};HWMP_EffectSerial=0;HWJ_Revision=nil
HWMP_ReleaseOwner(owner)
for i=20,50 do assert(ships.x.a[i]==0) end
HWMP_ReleaseOwner('gravwell:500')
for i=20,50 do assert(ships.x.a[i]==mod(i,2)) end
for _,value in ipairs({0,1,-3,0.75,0.65,1e-8,1048577,1e20}) do
 ships.x.speed=value
 HWMP_BlockGroup('x','gravwell:601',{AB_Attack},1)
 HWMP_EffectRecords={};HWMP_EffectSerial=0;HWJ_Revision=nil
 HWMP_ReleaseOwner('gravwell:601');assert(ships.x.speed==value)
end
-- Native death empties membership while preserving names. Later serial reuse
-- must not deserialize the empty marker belonging to the dead generation.
for name,members in pairs(groups) do groups[name]={} end
ships={};unit('new',1,1,1,0.9);groups.new={'new'}
HWMP_BlockGroup('new','gravwell:700',{AB_Move},1)
HWMP_ReleaseOwner('gravwell:700')
assert(ships.new.a[AB_Move]==1 and ships.new.speed==0.9)
""")
    return {
        "status": "passed",
        "world_mock": "warm/cold/overlap/mixed baselines/cooperation/sparse cache/extinction",
        "codec_mock": "31 abilities, arbitrary owner, integer/fixed/full-width speed roundtrip",
        "engine_tested": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify()))
