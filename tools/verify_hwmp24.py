"""Regression fixtures for HWMP24. Lua5.1 inspection is not engine validation.

Only Lua4's table iteration is translated in the test VM. Packaged code stays Lua4.
"""

import json
from pathlib import Path
import re
import shutil
import subprocess
from lupa.lua51 import LuaRuntime
from hwmp24 import (
    ROOT,
    WORK,
    SOURCE,
    RELEASE,
    DONOR,
    BUILD,
    CACHE,
    START_FLEET_INPUTS,
    equal_collector_start,
    index,
    sha,
    save,
)


def inspect_lua(text):
    return re.sub(
        r"\bfor\s+(\w+(?:\s*,\s*\w+)?)\s+in\s+([\w.]+)\s+do", r"for \1 in pairs(\2) do", text
    )


MOCK = r"""
getn=table.getn; tremove=table.remove; strsub=string.sub; strlen=string.len; strbyte=string.byte
max=math.max; mod=math.fmod; sqrt=math.sqrt; abs=math.abs
min=math.min;floor=math.floor;sort=table.sort;strfind=string.find;strchar=string.char;format=string.format
AB_Move=1; AB_Targeting=2; AB_Attack=3; AB_Dock=4; AB_Custom=5
AB_Hyperspace=6; AB_Scuttle=7; AB_Lights=8; AB_SpecialAttack=9; AB_Steering=10
COMMAND_Dock=11; COMMAND_Attack=12; COMMAND_Guard=13
groups={}; ships={}; orders={}; logs={}; now=0; dockRetries=0; tumbleClears={}
function unit(id,move,attack,scuttle,speed)
 ships[id]={a={[AB_Move]=move,[AB_Attack]=attack,[AB_Scuttle]=scuttle,
 [AB_Dock]=1,[AB_Targeting]=1,[AB_Custom]=1,[AB_Hyperspace]=0,[AB_Lights]=1},speed=speed}
end
function SobGroup_CreateIfNotExist(g) if groups[g]==nil then groups[g]={} end end
SobGroup_Create=SobGroup_CreateIfNotExist
function SobGroup_Exists(g) return groups[g]~=nil and 1 or 0 end
function SobGroup_FillSubstract(g,a,b)
 groups[g]={}
 for _,id in ipairs(groups[a] or {}) do
  local found=false;for _,other in ipairs(groups[b] or {}) do if id==other then found=true end end
  if not found then table.insert(groups[g],id) end
 end
end

function SobGroup_Clear(g) groups[g]={} end
function SobGroup_Count(g) return getn(groups[g] or {}) end
function SobGroup_Empty(g) if SobGroup_Count(g)==0 then return 1 else return 0 end end
function SobGroup_SobGroupAdd(g,other)
 SobGroup_CreateIfNotExist(g)
 for _,id in ipairs(groups[other] or {}) do
  local found=false;for _,old in ipairs(groups[g]) do if old==id then found=true end end
  if not found then table.insert(groups[g],id) end
 end
end
function SobGroup_Copy(g,other) SobGroup_Clear(g);SobGroup_SobGroupAdd(g,other) end
function SobGroup_GroupInGroup(a,b)
 for _,id in ipairs(groups[a] or {}) do
  local found=false;for _,candidate in ipairs(groups[b] or {}) do if candidate==id then found=true end end
  if not found then return 0 end
 end
 return 1
end
function SobGroup_FillShipsByIndexRange(g,source,start,count)
 for i=start+1,math.min(start+count,SobGroup_Count(source)) do table.insert(groups[g],groups[source][i]) end
end
function SobGroup_CanDoAbility(g,ability)
 for _,id in ipairs(groups[g] or {}) do if ships[id].a[ability]~=1 then return 0 end end
 return 1
end
function SobGroup_AbilityActivate(g,ability,value)
 for _,id in ipairs(groups[g] or {}) do ships[id].a[ability]=value end
end
function SobGroup_GetSpeed(g) return ships[groups[g][1]].speed end
function SobGroup_SetSpeed(g,speed) for _,id in ipairs(groups[g] or {}) do ships[id].speed=speed end end
function SobGroup_ClearTumble(g) for _,id in ipairs(groups[g] or {}) do tumbleClears[id]=(tumbleClears[id] or 0)+1 end end
function SobGroup_IsDoingAbility(g,ability) return (orders[g] or {})[ability] or 0 end
function SobGroup_GetCurrentOrder(g) return (orders[g] or {}).command end
function SobGroup_IsDocked(g) return (orders[g] or {}).docked or 0 end
function SobGroup_UnderAttack(g) return (orders[g] or {}).under or 0 end
function SobGroup_GetActualSpeed(g) return (orders[g] or {}).actual or 0 end
function SobGroup_DockSobGroupWithAny(g) dockRetries=dockRetries+1 end
function Universe_GameTime() return now end
function Universe_PlayerCount() return 3 end
function Player_IsAlive(i) if i==2 then return 0 else return 1 end end
function AreAllied(a,b) if a==b or b==1 then return 1 else return 0 end end
function print(...) end
function FX_StartEvent(...) end
"""


def vm_for(source=SOURCE):
    vm = LuaRuntime(register_eval=False, register_builtins=False)
    vm.execute(MOCK)

    def load(name):
        assert name.startswith("data:"), name
        relative = name[5:].lower()
        path = index(source).get(relative) or index(DONOR).get(relative)
        if path is None:
            raise AssertionError("Missing runtime dependency: " + name)
        vm.execute(inspect_lua(path.read_text(encoding="ascii")))

    vm.globals().dofilepath = load
    load("data:scripts/playerspatch/ships_util/core/global.lua")
    return vm, load


def check_effects():
    vm, load = vm_for()
    vm.execute("""
unit('a',0,1,0,0.65);unit('b',1,0,1,1.25)
groups.g={'a','b'};groups.a={'a'};groups.b={'b'}
HWMP_BlockGroup('g','gravwell:1',{AB_Move,AB_Attack,AB_Dock},1)
HWMP_BlockGroup('b','gravwell:2',{AB_Move,AB_Attack,AB_Dock},1)
HWMP_BlockGroup('g','gravwell:1',{AB_Move,AB_Attack,AB_Dock},1)
HWMP_ReleaseOwner('gravwell:1')
assert(ships.a.a[AB_Move]==0 and ships.a.a[AB_Attack]==1 and ships.a.speed==0.65)
assert(ships.b.a[AB_Move]==0 and ships.b.speed==0)
HWMP_ReleaseOwner('gravwell:2')
assert(ships.b.a[AB_Move]==1 and ships.b.a[AB_Attack]==0 and ships.b.speed==1.25)
-- Mixed entry baselines and an evolving mission prohibition.
HWMP_BlockGroup('g','gravwell:3',{AB_Move,AB_Attack},1)
HWMP_SetAbilityAllowed('b',AB_Move,0);HWMP_SetAbilityAllowed('a',AB_Move,1)
HWMP_SetSpeedAllowed('b',0.8)
assert(ships.a.a[AB_Move]==0 and ships.b.speed==0)
HWMP_UnblockGroup('a','gravwell:3')
assert(ships.a.a[AB_Move]==1 and ships.b.a[AB_Move]==0)
HWMP_ReleaseOwner('gravwell:3')
assert(ships.b.a[AB_Move]==0 and ships.b.speed==0.8)
-- Transport and salvage cannot override pre-existing or other effect locks.
HWMP_BlockGroup('g','transport:1',{AB_Dock,AB_Scuttle,AB_Attack},0)
HWMP_BlockGroup('g','gravwell:4',{AB_Dock,AB_Attack},1)
HWMP_ReleaseAbility('g','transport:1',AB_Dock)
assert(ships.a.a[AB_Dock]==0)
HWMP_ReleaseOwner('transport:1');HWMP_ReleaseOwner('gravwell:4')
assert(ships.a.a[AB_Scuttle]==0 and ships.b.a[AB_Scuttle]==1)
orders.g={[AB_Dock]=1};SobGroup_NoSalvageScuttle('g')
orders.g={};SobGroup_NoSalvageScuttle('g')
assert(ships.a.a[AB_Scuttle]==0 and ships.b.a[AB_Scuttle]==1)
-- Tumble belongs to gravitational fields, not unrelated transport locks.
HWMP_BlockGroup('g','gravwell:5',{AB_Move},1)
HWMP_BlockGroup('b','gravwell:6',{AB_Move},1)
HWMP_BlockGroup('a','transport:2',{AB_Dock},0)
HWMP_ClearReleasedTumble('g','gravwell:5')
assert(tumbleClears.a==1 and tumbleClears.b==nil)
HWMP_ReleaseOwner('gravwell:5');HWMP_ReleaseOwner('gravwell:6');HWMP_ReleaseOwner('transport:2')
""")
    # Reload must not reset the saved baselines/owner state.
    vm.execute("HWMP_BlockGroup('b','gravwell:7',{AB_Attack},1)")
    load("data:scripts/hwmp24/effects.lua")
    vm.execute(
        "HWMP_ReleaseOwner('gravwell:7');assert(ships.b.a[AB_Attack]==0 and ships.b.speed==0.8)"
    )
    load("data:scripts/playerspatch/ships_util/core/memgroup.lua")
    load("data:scripts/playerspatch/ships_util/lib/gravwells.lua")
    vm.execute("""
unit('gw',1,1,1,1);groups.gw={'gw'}
GW_MEM:Start('gw',0,55)
local instance=GW_MEM:Get('gw',0,55)
instance:StunGroup('a',1);instance:StunGroup('b',1)
HWMP_BlockGroup('b','gravwell:56',{AB_Move,AB_Attack},1)
instance.TumbleGroup=function(self,g,t) if t==0 then HWMP_ClearReleasedTumble(g,'gravwell:'..self.ship_id) end end
SobGroup_Copy(instance.previously_stunned,'g')
GW_MEM:Destroy('gw',0,55)
assert(ships.gw.a[AB_Hyperspace]==0 and ships.a.a[AB_Move]==1)
assert(ships.b.a[AB_Move]==0 and ships.b.speed==0)
HWMP_ReleaseOwner('gravwell:56');assert(ships.b.speed==0.8)
local count=getn(GW_MEM_PROTO.target_types)
HWMP_RegisterGravityTarget('new_fighter');HWMP_RegisterGravityTarget('new_fighter')
assert(getn(GW_MEM_PROTO.target_types)==count+1)
""")
    return "overlap/mixed baselines/mission changes/transport/salvage/destruction/reload passed"


def check_groups_and_dock():
    vm, _ = vm_for()
    vm.execute("""
groups.empty={};assert(getn(SobGroup_Split('empty'))==0)
groups.g={'a','b','c','d','e'}
local split=SobGroup_Split('g',2)
assert(getn(split)==3 and SobGroup_Count(split[1])==2 and SobGroup_Count(split[3])==1)
unit('a',1,1,1,1);groups.a={'a'}
orders.a={command=COMMAND_Dock,under=1,actual=0}
now=0;SobGroup_UnderAttackReissueDock('a')
now=2;SobGroup_UnderAttackReissueDock('a');assert(dockRetries==0)
now=3;SobGroup_UnderAttackReissueDock('a');assert(dockRetries==1)
now=7;SobGroup_UnderAttackReissueDock('a');assert(dockRetries==1)
now=8;SobGroup_UnderAttackReissueDock('a');assert(dockRetries==2)
orders.a.actual=2;now=12;SobGroup_UnderAttackReissueDock('a');assert(dockRetries==2)
orders.a.actual=0;now=13;SobGroup_UnderAttackReissueDock('a')
ships.a.a[AB_Move]=0;now=20;SobGroup_UnderAttackReissueDock('a');assert(dockRetries==2)
ships.a.a[AB_Move]=1;orders.a.docked=1;SobGroup_UnderAttackReissueDock('a');assert(dockRetries==2)
groups.Player_Ships0={'a'};groups.Player_Ships1={'b'};groups.Player_Ships2={'dead'}
local active=Universe_GetAllActiveShips();assert(SobGroup_Count(active)==2)
groups.Player_Ships0={};active=Universe_GetAllActiveShips();assert(SobGroup_Count(active)==1 and groups[active][1]=='b')
""")
    vm.execute((ROOT.parent / "tools/fixtures/dock_identity.lua").read_text(encoding="ascii"))
    return "empty/dense split, bounded stalled dock retry with independent hull IDs, active ship refresh passed"


def check_defense():
    vm, load = vm_for()
    load("data:ship/tai_defensefighter/tai_defensefighter.lua")
    vm.execute("""
selections={};missiles={};attacks={};guardOrders={}
function Selection_Create(s) selections[s]={} end
function Selection_GetMissiles(s) for _,m in ipairs(missiles) do table.insert(selections[s],m) end;return getn(selections[s]) end
function Selection_FilterInclude(dst,src,filter,arg,range)
 local result={}
 for _,m in ipairs(selections[src]) do
  if (filter=='NearPoint' and m.range<=tonumber(range)) or (filter=='PlayerOwner' and m.owner==tonumber(arg)) then table.insert(result,m) end
 end
 selections[dst]=result;return getn(result)
end
function Selection_FilterExclude(dst,src,filter,arg,unused)
 local result={};for _,m in ipairs(selections[src]) do if m.owner~=tonumber(arg) then table.insert(result,m) end end
 selections[dst]=result;return getn(result)
end
function SobGroup_GetPosition(g) return {0,0,0} end
function SobGroup_AttackSelection(p,g,s,flag) local ids={};for _,m in ipairs(selections[s]) do table.insert(ids,m.id) end;table.insert(attacks,ids) end
function SobGroup_GetCommandTargets(dst,g,command) if command==COMMAND_Guard then groups[dst]={'capital'} else groups[dst]={} end end
function SobGroup_GuardSobGroup(g,target) table.insert(guardOrders,groups[target][1]) end
groups.df={'df'};orders.df={command=COMMAND_Guard}
missiles={{id='old',owner=0,range=100},{id='friend',owner=1,range=100},{id='enemy1',owner=2,range=4000}}
updateDefenseFighter('df',0,10)
assert(getn(attacks)==1 and getn(attacks[1])==1 and attacks[1][1]=='enemy1')
-- Same total count, entirely different local target, and no ship attack target.
orders.df.command=COMMAND_Attack
missiles={{id='far',owner=2,range=8000},{id='friend2',owner=1,range=100},{id='enemy2',owner=2,range=200}}
updateDefenseFighter('df',0,10)
assert(getn(attacks)==2 and getn(attacks[2])==1 and attacks[2][1]=='enemy2')
missiles={};updateDefenseFighter('df',0,10)
assert(getn(attacks)==2 and guardOrders[1]=='capital')
""")
    return (
        "same-count target replacement, ally/range filters, missile-only order, guard return passed"
    )


def check_transport():
    from hwrm_common import PROJECT

    vm, load = vm_for()
    load("data:scripts/playerspatch/ships_util/lib/frigates.lua")
    vm.execute((PROJECT / "tools/fixtures/transport.lua").read_text(encoding="ascii"))
    for race, label in (("kus", "Kus"), ("tai", "Tai")):
        load(f"data:ship/{race}_supportfrigate/{race}_supportfrigate.lua")
        vm.execute(
            "ships.carrier.real=1;ships.a.real=1;ships.b.real=1;ships.a.docked=1;ships.b.docked=1"
        )
        vm.globals()[f"Create_{label}_SupportFrigate"]("carrier", 0, 51)
        vm.execute(
            "ships.carrier.real=0;SupportFrigate_HyperspaceDock('carrier',51);SupportFrigate_HyperspaceDock('carrier',51)"
        )
        vm.execute("deferSpawn=true")
        vm.globals()[f"Destroy_{label}_SupportFrigate"]("carrier", 0, 51)
        vm.execute(
            "assert(ships.a.real==0 and ships.b.real==0 and ships.a.hidden==0 and ships.b.hidden==0);assert(ships.a.selectable==1 and ships.b.selectable==1);finishSpawns();deferSpawn=false"
        )
        vm.execute(
            "assert(ships.a.real==1 and ships.b.real==1 and ships.a.hidden==0 and ships.b.hidden==0);assert(ships.a.a[AB_Attack]==0 and ships.b.a[AB_Attack]==1 and ships.b.a[AB_Scuttle]==0 and ships.b.a[AB_Dock]==1);assert(HWMP_TransportAnchors[51]==nil)"
        )
    vm.execute((PROJECT / "tools/fixtures/salvage.lua").read_text(encoding="ascii"))
    return "mock: stalled redock does not retain visibility/locks; mixed baselines/other owner native pre-disabled salvage/identity/other-owner mocks and deferred-Spawn recovery on both destruction callbacks passed"


def check_tooltips():
    from production_data import RACES, catalog, effective_files

    rows, expected, _ = catalog(SOURCE)
    definitions = effective_files(SOURCE)
    checks = []
    from language_data import LANGUAGES

    for language in LANGUAGES:
        vm = LuaRuntime(register_eval=False, register_builtins=False)
        vm.execute(
            "strsub=string.sub;function doscanpath(...) end;function GetProductionTimeSetting() return 2 end"
        )

        def load(name):
            path = SOURCE / (
                "locale/" + language + "/" + name[7:] if name.startswith("locale:") else name[5:]
            )
            vm.execute(inspect_lua(path.read_text(encoding="ascii")))

        vm.globals().dofilepath = load
        load("data:scripts/hwmp24/tooltips.lua")
        labels = dict(vm.globals().HWMP_TooltipLocalization.items())
        assert labels
        known = next(iter(labels))
        vm.globals().known = known
        vm.execute(
            'build={{ThingToBuild="unknown",Description="$999999999"},{ThingToBuild="new",Description=known},{ThingToBuild="nil"}};research={{Description="$999999999",Time=1},{Description=known,Time=3,UpgradeValue=1.25}}'
        )

        # Actual build table is upstream. Add a fixture for an added/unknown description.
        def fixture_load(name):
            load(name)
            if name.endswith("/buildtimes.lua"):
                vm.execute('buildtimes.unknown=5;buildtimes.new=7;buildtimes["nil"]=1')

        vm.globals().dofilepath = fixture_load
        load("data:scripts/productiontimes/applybuildtimes.lua")
        load("data:scripts/productiontimes/applyresearchtimes.lua")
        vm.execute(
            'assert(build[1].Description=="$999999999" and build[3].Description==nil);assert(research[1].Description=="$999999999");assert(string.find(build[2].Description,HWMP_TooltipBaseTimeLabel,1,true));assert(string.find(research[2].Description,"+25%",1,true))'
        )
        if language == "Russian":
            assert vm.globals().HWMP_TooltipBaseTimeLabel == "Базовое время"
        checks.append(language)
        # Exercise actual race build tables through the packaged Lua callback.
        vm.globals().dofilepath = load
        for race in RACES:
            vm.execute(
                definitions[f"scripts/races/{race}/scripts/def_build.lua"].read_text(
                    encoding="ascii"
                )
            )
            original = {i: row.Description for i, row in vm.globals().build.items()}
            load("data:scripts/productiontimes/applybuildtimes.lua")
            for i, row in vm.globals().build.items():
                text = original[i]
                if text:
                    assert text in labels, (language, race, row.ThingToBuild, text)
                    assert labels[text] in row.Description
                    assert (
                        "</b>  "
                        + format(expected[row.ThingToBuild], "g")
                        + vm.globals().HWMP_TooltipSecondsLabel
                    ) in row.Description
                else:
                    assert row.Description == text, (race, row.ThingToBuild)
        vm.execute(
            'build={{ThingToBuild="Hgn_MS_Module_Research",Description=""}};research={{Description="",Time=75}}'
        )
        load("data:scripts/productiontimes/applybuildtimes.lua")
        load("data:scripts/productiontimes/applyresearchtimes.lua")
        vm.execute('assert(build[1].Description=="" and research[1].Description=="")')
    return checks


def verify_source():
    manifest = json.loads((WORK / "manifest.json").read_text(encoding="utf8"))
    files = index(SOURCE)
    upstream = index(DONOR)
    overrides = index(ROOT / "overrides")
    dock_callbacks = []
    for name, path in upstream.items():
        if name.startswith("ship/") and name.endswith(".lua"):
            before = path.read_text(encoding="ascii")
            old = "SobGroup_UnderAttackReissueDock(CustomGroup)"
            if old in before:
                assert before.count(old) == 1, name
                assert (
                    files[name].read_text(encoding="ascii").replace("\r\n", "\n").strip()
                    == before.replace(old, "SobGroup_UnderAttackReissueDock(CustomGroup, shipID)")
                    .replace("\r\n", "\n")
                    .strip()
                ), name
                dock_callbacks.append(name)
    assert len(dock_callbacks) == 11, dock_callbacks
    assert manifest["files"] == {n: sha(p) for n, p in files.items()}
    for name in manifest["base_runtime_files"]:
        if name in overrides:
            assert sha(files[name]) == sha(overrides[name])
        elif upstream[name].stat().st_size == 0 and name.endswith(".lua"):
            assert files[name].read_text() == "-- Intentionally empty upstream Lua file.\n"
        else:
            assert sha(files[name]) == sha(upstream[name]), name
    for name, path in overrides.items():
        assert sha(files[name]) == sha(path)
    expected_starts = {"scripts/startingfleets/" + row[0] for row in START_FLEET_INPUTS}
    assert {n for n in overrides if n.startswith("scripts/startingfleets/")} == expected_starts
    for filename, folder, digest in START_FLEET_INPUTS:
        name = "scripts/startingfleets/" + filename
        original = CACHE / "players-patch-audit" / folder / name
        assert sha(original) == digest
        assert files[name].read_text(encoding="ascii") == equal_collector_start(
            original.read_text(encoding="ascii")
        )
        for prefix, expected in (("vaygr", 6), ("hiigaran", 6)):
            candidate = (
                files[name]
                if prefix == "vaygr"
                else CACHE
                / "players-patch-audit"
                / folder
                / "scripts/startingfleets"
                / filename.replace("vaygr", "hiigaran")
            )
            vm = LuaRuntime(unpack_returned_tuples=True)
            vm.execute(candidate.read_text(encoding="ascii"))
            collectors = [
                s
                for _, s in vm.globals().PersistantData.Squadrons.items()
                if s.type.lower().endswith("_resourcecollector")
            ]
            assert len(collectors) == 1 and collectors[0].number == expected, (filename, prefix)
    assert not any(n.startswith(("leveldata/campaign/vastreaches", "weapon/nkr_")) for n in files)
    expected_weapons = {
        "weapon/vgr_heavyfusionmissilelauncherturret/vgr_heavyfusionmissilelauncherturret.wepn",
        "weapon/vgr_concussionmissilelauncher/vgr_concussionmissilelauncher.wepn",
    }
    assault_weapons = set()
    for suffix in ("bottom", "left", "right"):
        weapon = "vgr_flechettecannonassaultfrigate" + suffix
        name = f"weapon/{weapon}/{weapon}.wepn"
        before = upstream[name].read_text(encoding="ascii")
        assert before.count("487, 1.2, 535, 4.0);") == 1
        assert files[name].read_text(encoding="ascii") == before.replace(
            "487, 1.2, 535, 4.0);", "487, 1.2, 535, 1.2);"
        )
        assault_weapons.add(name)
    expected_weapons.update(assault_weapons)
    assert {
        n for n, p in overrides.items() if p.suffix in (".ship", ".wepn", ".subs", ".miss")
    } == expected_weapons
    wf_name = "scripts/weaponfire/vgr_mediummissile/vgr_mediummissile.wf"
    assert {n for n, p in overrides.items() if p.suffix == ".wf"} == {wf_name}
    assert 'scartype = "Vgr_MediumMissile/Vgr_MediumMissile"' in files[wf_name].read_text(
        encoding="ascii"
    )
    assert all(
        ("missile/vgr_mediummissile/vgr_mediummissile" + ext) in files
        for ext in (".miss", ".hod", ".events")
    )
    default = "scripts/races/vaygr/scripts/research/default.lua"
    expected, n = re.subn(
        r'(?m)^(\s*Name\s*=\s*)"Scout speed limiter"',
        r'\1"ScoutSpeedLimiter"',
        upstream[default].read_text(encoding="ascii"),
    )
    assert n == 1 and files[default].read_text(encoding="ascii") == expected
    assert "scripts/save.lua" not in overrides, "Do not ship the ineffective serializer experiment"
    from audit_missiles import verify_fixes

    weapon_fixes = verify_fixes(SOURCE)
    from production_data import verify as verify_data
    from verify_effect_journal import verify as verify_journal

    result = {
        "status": "passed",
        "production_data": verify_data(SOURCE),
        "files": len(files),
        "fix_revision": manifest["fix_revision"],
        "starting_collectors": {
            "hiigaran": 6,
            "vaygr": 6,
            "changed_files": sorted(expected_starts),
            "other_start_fields_unchanged": True,
        },
        "upstream_combat_definitions": "two missile corrections, restored Medium weaponfire and approved Assault final speed node; other combat coefficients unchanged",
        "weapon_fixes": weapon_fixes,
        "assault_fix": {
            "last_speed_node": [535, 1.2],
            "weapons": sorted(assault_weapons),
            "all_other_normalized_text_unchanged": True,
        },
        "effect_regression": check_effects(),
        "effect_checkpoint_journal": verify_journal(vm_for),
        "groups_and_dock": check_groups_and_dock(),
        "missile_defense": check_defense(),
        "transport": check_transport(),
        "research_id_fix": "ScoutSpeedLimiter internal ID only; cost/time/effect and display names unchanged",
        "tooltips": check_tooltips(),
        "engine_tested": False,
        "installed": False,
    }
    save(WORK / "verification-source.json", result)
    print(json.dumps(result))
    return result


def verify_archive(archive):
    from hwrm_archive import TOOL, native_aliases
    from hwrm_common import short_path

    archive = Path(archive)
    sources = index(SOURCE)
    results = []
    from language_data import LANGUAGES

    for path, language in [
        (archive, None),
        *[(archive.parent / (language + ".big"), language) for language in LANGUAGES],
    ]:
        target = BUILD / ("extracted-" + (language or "main"))
        assert target.resolve().is_relative_to(BUILD.resolve())
        if target.exists():
            shutil.rmtree(target)
        target.mkdir()
        proc = subprocess.run(
            [str(TOOL), "-a", str(path), "-e", short_path(target)], capture_output=True, text=True
        )
        save(
            WORK / (target.name + "-log.json"),
            {"exit": proc.returncode, "log": proc.stdout + proc.stderr},
        )
        assert proc.returncode == 0, (path, proc.returncode)
        expected = {}
        for name, source in sources.items():
            if not name.startswith("locale/"):
                if language is None:
                    expected[name] = sha(source)
            elif name.startswith("locale/" + (language or "English").lower() + "/"):
                expected[name.split("/", 2)[2]] = sha(source)
        assert {name: sha(p) for name, p in index(target).items()} == expected, path
        results.append(
            {
                "archive": str(path),
                "sha256": sha(path),
                "files": len(expected),
                "aliases": native_aliases(path),
            }
        )
    report = {
        "status": "passed",
        "archives": results,
        "full_extract_hash_comparison": True,
        "engine_tested": False,
        "installed": False,
    }
    save(WORK / "verification-package.json", report)
    print(json.dumps(report))
    return report


if __name__ == "__main__":
    verify_source()
