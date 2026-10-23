"""Check diagnostic composition, Lua4 parsing and SCAR control-flow fixtures.

Fixtures do not model native weapons, gravity callbacks, movement or research.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
from lupa.lua51 import LuaRuntime
from hwrm_common import index, save, sha
from testgrounds import SOURCE, WORK, ROOT, MISSIONS, COLLECTION, digest_tree, read_ucs
from collect_testgrounds import collect

MOCK = r'''
getn=table.getn; sqrt=math.sqrt; mod=math.fmod
AB_Move=1; AB_Attack=2; AB_Dock=3; AB_Custom=4; AB_Builder=5
ONEKEY=1; TWOKEY=2; THREEKEY=3; PassiveROE=0; NeutralStance=1; EvasiveStance=2
OT_Primary=0; OS_Complete=1; now=0; attacks=0; moves=0; kills=0; grants=0
groups={}; logs={}; keys={}; removed=0
function Universe_GameTime() return now end
function print(s) table.insert(logs,s) end
function SobGroup_Count(g) return groups[g].n end
function SobGroup_GetPosition(g) return groups[g].p end
function SobGroup_HealthPercentage(g) return groups[g].hp end
function SobGroup_CurrentHealthTotal(g) return groups[g].hp*10000 end
function SobGroup_CanDoAbility(g,a) if groups[g].a[a]==nil then return 1 end return groups[g].a[a] end
function SobGroup_AbilityActivate(g,a,v) groups[g].a[a]=v end
function SobGroup_SetInvulnerability(g,v) groups[g].inv=v end
function SobGroup_SetROE(g,v) groups[g].roe=v end
function SobGroup_SetStance(g,v) groups[g].stance=v end
function SobGroup_Stop(p,g) groups[g].stopped=1 end
function SobGroup_Move(p,g,v) moves=moves+1;groups[g].move_volume=v;groups[g].move_owner=p end
function SobGroup_Attack(p,g,t) attacks=attacks+1;groups[g].target=t end
function SobGroup_TakeDamage(g,v) kills=kills+1;groups[g].hp=0;groups[g].n=0 end
function Player_UnrestrictResearchOption(p,t) end
function Player_GrantResearchOption(p,t) grants=grants+1;grant_player=p;grant_name=t end
function CPU_Enable(p,v) end
function FOW_RevealGroup(g,v) end
function Camera_Interpolate(a,b,c) end
function Objective_Add(t,k) return 1 end
function Objective_AddDescription(i,t) end
function Objective_SetState(i,s) end
function UI_BindKeyEvent(k,v) keys[k]=v end
function Subtitle_Message(s,t) end
function Rule_AddInterval(f,t) end
function Rule_Remove(f) removed=removed+1 end
function Selection_Create(s) end
function Selection_GetMissiles(s) return 3 end
'''


def check(luac=None):
    source = json.loads((WORK/'source.json').read_text(encoding='utf8'))
    files = index(SOURCE)
    actual = digest_tree(SOURCE)
    assert actual == {**source['base_files'], **source['additions']}, 'Source receipt mismatch'
    assert digest_tree(Path(source['base_source'])) == source['base_files'], 'Prepared base changed'
    additions = {n:p for n,p in files.items() if n in source['additions']}
    snippets = [p for n,p in additions.items() if p.suffix in ('.lua','.level','.campaign')]
    parse = {'status':'not_run','engine_tested':False}
    if luac:
        compiler = Path(luac).resolve(strict=True)
        version = subprocess.run([str(compiler),'-v'],capture_output=True,text=True)
        assert 'Lua 4.0.1' in version.stdout+version.stderr, 'Require Lua4.0.1 parser'
        for path in snippets:
            proc = subprocess.run([str(compiler),'-p',str(path)],capture_output=True,text=True)
            assert proc.returncode == 0, (path,proc.stdout,proc.stderr)
        bad = WORK/'mixed-table-must-fail.lua'
        bad.write_text('return {name="x", 1}\n',encoding='ascii')
        proc = subprocess.run([str(compiler),'-p',str(bad)],capture_output=True,text=True)
        assert proc.returncode != 0, 'Compiler failed to reject the known Lua4 mixed-table incompatibility'
        parse = {'status':'passed','files':len(snippets),'compiler_sha256':sha(compiler),
                 'version':(version.stdout+version.stderr).strip(),'mixed_table_rejected':True,
                 'engine_tested':False}
    menu = LuaRuntime()
    menu.execute((SOURCE/f'leveldata/campaign/{COLLECTION}.campaign').read_text())
    g = menu.globals()
    assert g.contentType == 2 and g.contentName == COLLECTION and g.contentRules == 'SinglePlayer'
    assert len(g.Mission) == 3 and g.ExtFilter == 'campaign_gbx'
    ucs = {}
    for lang in ('English','Russian'):
        text = read_ucs(SOURCE/f'locale/{lang}/hwmp_testgrounds.ucs')
        pairs = [line.split('\t',1) for line in text.splitlines() if line.strip()]
        assert len(pairs) == len(dict(pairs)) == source['strings']
        ucs[lang] = dict(pairs)
    assert set(ucs['English']) == set(ucs['Russian'])
    assert all(ucs['English'][n] != ucs['Russian'][n] for n in ucs['English'])
    for n, path in additions.items():
        if path in snippets:
            for number in re.findall(r'\$(9984\d+)',path.read_text()): assert number in ucs['English']
    results=[]
    sample_log=[]
    for chapter, script, title, desc in MISSIONS:
        for filename in (chapter+'.lua', chapter+'.level'):
            assert (SOURCE/f'leveldata/campaign/{COLLECTION}/{chapter}/{filename}').is_file()
        assert (SOURCE/f'ui/mapthumbnails/campaign/{COLLECTION}/{chapter}.dds').is_file()
        # Run the level declaratively to check group names, owners and volume references.
        vm=LuaRuntime(); seen={}; volumes=set()
        def squad(name, kind, pos, owner, orientation, size, flags):
            assert name not in seen
            seen[name]=(kind,owner,size)
        vm.globals().addSquadron=squad
        vm.globals().addSphere=lambda name,pos,r: volumes.add(name)
        for fun in ('createSOBGroup','addToSOBGroup','addCamera','setWorldBoundsInner','loadBackground','setSensorsManagerCameraDistances'):
            vm.globals()[fun]=lambda *args: None
        vm.execute((SOURCE/f'leveldata/campaign/{COLLECTION}/{chapter}/{chapter}.level').read_text())
        vm.globals().DetermChunk(); vm.globals().NonDetermChunk()
        assert set(seen) == {ship[0] for ship in source['fixtures'][chapter]}
        for variant in (('default','control','control_primary_loss','missing_primary','no_selection') if script == 'missiles' else ('default',)):
            lua=LuaRuntime(); lua.execute(MOCK); lg=lua.globals()
            for name, kind, pos, owner, size in source['fixtures'][chapter]:
                lg.groups[name]=lua.table_from({'n':1,'p':lua.table_from(pos),'hp':1,'a':lua.table()})
            def load(path):
                name=path.lower().removeprefix('data:')
                if name == 'scripts/scar/scar_util.lua': return
                assert name in additions, 'Unexpected script dependency: '+name
                lua.execute(files[name].read_text())
            lg.dofilepath=load
            load('data:scripts/hwmp24/testgrounds/'+script+'.lua'); lg.OnInit()
            assert lg.HWT_DONE == 0 and lg.HWT_STARTED == 0
            if script == 'gravity':
                lg.HWT_GravityMarker(); lg.HWT_Tick()
                assert lg.groups['HWT_KusEnemy'].a[lg.AB_Attack] == 0
                assert lg.SobGroup_CanDoAbility('HWT_KusFriendly',lg.AB_Attack) == 1
                lg.HWT_GravityDestroy()
                assert lg.kills == 2 and lg.HWT_MARKER == 1
            elif script == 'assault':
                assert lg.grants == 1 and lg.grant_player == 2 and lg.grant_name == 'InterceptorMAXSPEEDUpgrade1'
                assert len(volumes) == 4
                lg.HWT_AssaultStart(); lg.HWT_AssaultStart()
                assert lg.attacks == 4 and lg.moves == 4
                for i in range(1,5):
                    target=lg.groups['HWT_Target'+str(i)]
                    assert target.stance == (2 if i%2==0 else 1)
                    assert target.move_owner == (1 if i<3 else 2)
                    assert target.move_volume in volumes
                lg.now=46; lg.HWT_Tick()
                assert lg.HWT_DONE == 1 and lg.removed == 1
            else:
                if variant == 'no_selection': lg.Selection_GetMissiles=None
                lg.HWT_MissileStart(); lg.HWT_MissileStart()
                assert lg.attacks == 1
                if variant == 'control':
                    lg.now=46; lg.HWT_Tick()
                    assert lg.kills == 0 and lg.HWT_DONE == 1
                    lg.HWT_MissileKill()
                    assert lg.kills == 0, 'Completed control must reject a late kill trigger'
                elif variant == 'control_primary_loss':
                    lg.groups['HWT_Primary'].n=0
                    lg.now=2; lg.HWT_Tick()
                    assert lg.kills == 0 and lg.HWT_DONE == 1
                elif variant == 'missing_primary':
                    lg.groups['HWT_Primary'].n=0
                    lg.HWT_MissileKill()
                    assert lg.kills == 0 and lg.HWT_KILLED == 0
                else:
                    lg.now=4; lg.HWT_Tick(); lg.HWT_MissileKill(); lg.HWT_MissileKill()
                    assert lg.kills == 1 and lg.HWT_KILLED == 1
                    assert lg.groups['HWT_Launcher'].a[lg.AB_Attack] == 0
                    lg.now=40; lg.HWT_Tick()
                    assert lg.HWT_DONE == 1
            sample_log.extend(lg.logs[i] for i in range(1,len(lg.logs)+1))
            results.append({'mission':script,'fixture':variant,'status':'passed','engine_tested':False})
    mock_path=WORK/'synthetic-mock.log'
    mock_path.write_text('\n'.join(sample_log)+'\n',encoding='utf8')
    parsed=collect(mock_path,source['revision'])
    assert len(parsed['runs']) == len(results) and parsed['status'] == 'observation_only'
    assert not parsed['native_test_plan_updated'] and not parsed['physical_hull_count_inferred']
    try: collect(mock_path,'wrong')
    except ValueError: pass
    else: raise AssertionError('Stale log revision accepted')
    report={'status':'passed','revision':source['revision'],'base_runtime_unchanged':True,
            'menu_chapters':3,'ru_en_pairs':source['strings'],'lua4':parse,'control_flow_mocks':results,
            'collector':'passed; synthetic only; no native passes','engine_tested':False,'installed':False}
    save(WORK/'verification-source.json',report)
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--luac',type=Path)
    args=p.parse_args(); print(json.dumps(check(args.luac),ensure_ascii=False,indent=2))
