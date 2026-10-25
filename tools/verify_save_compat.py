"""Validate research hash identifiers and temporary-effect stock-save roundtrip."""
import json
import re
import subprocess
from hwrm_common import CACHE,PROJECT,index,sha,save
from verify_hwmp24 import vm_for,inspect_lua,SOURCE,DONOR


def verify():
    compiler=CACHE/'hwmp-testgrounds-step/lua4/lua-4.0.1/luac4-x86.exe'
    work=PROJECT/'local/auto-tests/save-compatibility';work.mkdir(parents=True,exist_ok=True)
    native={}
    for folder in ('rm-base','rm-hw1','rm-hw2','test'):native.update(index(CACHE/'players-patch-audit'/folder))
    native.update(index(SOURCE))
    names=[]
    for name,path in native.items():
        if name.startswith('scripts/races/') and '/scripts/research/' in name and name.endswith('.lua'):
            names.extend(re.findall(r'(?m)^\s*Name\s*=\s*"([^"\n]+)"',path.read_text(encoding='utf-8-sig')))
    assert len(names)>100
    invalid=sorted(set(n for n in names if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',n)))
    assert not invalid,invalid
    default='scripts/races/vaygr/scripts/research/default.lua'
    expected,count=re.subn(r'(?m)^(\s*Name\s*=\s*)"Scout speed limiter"',r'\1"ScoutSpeedLimiter"',(DONOR/default).read_text(encoding='ascii'))
    assert count==1 and (SOURCE/default).read_text(encoding='ascii')==expected
    bad=work/'old-hash.lua';bad.write_text('SCOUT SPEED LIMITER = 3943337165\n',encoding='ascii')
    good=work/'research-hashes.lua';good.write_text(''.join(n.upper()+' = 0\n' for n in sorted(set(names))),encoding='ascii')
    def parse(path):return subprocess.run([str(compiler),'-p',str(path)],capture_output=True,text=True)
    assert parse(bad).returncode!=0 and parse(good).returncode==0
    stock=CACHE/'players-patch-audit/rm-base/scripts/save.lua'
    assert sha(stock)=='36f72eb35332ae0f8fd9b3a6bc93e5b9d85a67386b39b32de974870c5c9eab45'
    vm,load=vm_for();output=[]
    vm.globals().write=lambda *args:output.extend(str(x) for x in args)
    vm.execute('format=string.format;function flush() end')
    vm.execute(inspect_lua(stock.read_text(encoding='ascii').split('writeto(saveOutputFile)')[0]))
    vm.execute('''
unit('saved',1,0,1,0.75);groups.saved={'saved'}
HWMP_BlockGroup('saved','gravwell:1',{AB_Move,AB_Attack},1)
HWMP_BlockGroup('saved','gravwell:2',{AB_Move,AB_Attack},1)
assert(HWMP_OwnerKey('a:b')~=HWMP_OwnerKey('a_b'))
assert(HWMP_OwnerKey('a-b')~=HWMP_OwnerKey('a_b'))
''')
    vm.globals().saveVar('HWMP_EffectRecords',vm.globals().HWMP_EffectRecords)
    vm.globals().saveVar('HWMP_EffectSerial',vm.globals().HWMP_EffectSerial)
    text=''.join(output);path=work/'effect-state.lua';path.write_text(text,encoding='ascii')
    assert parse(path).returncode==0
    vm.execute('HWMP_EffectRecords=nil;HWMP_EffectSerial=nil');load('data:scripts/hwmp24/effects.lua');vm.execute(text)
    vm.execute('''
HWMP_ReleaseOwner('gravwell:1');assert(ships.saved.a[AB_Move]==0 and ships.saved.speed==0)
HWMP_ReleaseOwner('gravwell:2');assert(ships.saved.a[AB_Move]==1 and ships.saved.a[AB_Attack]==0 and ships.saved.speed==0.75)
''')
    report={'research_names_checked':len(names),'unsafe_ids':invalid,'old_scout_hash_reproduces_parse_failure':True,
            'only_internal_scout_name_changed':True,'stock_save_lua_sha256':sha(stock),'effect_roundtrip_and_lua4_parse':True,'native_save_load':False}
    save(work/'verification.json',report);return report


if __name__=='__main__':print(json.dumps(verify(),indent=2))
