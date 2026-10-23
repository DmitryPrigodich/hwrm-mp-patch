"""Pinned missile data/attachment audit. Nominal damage is not measured damage.

Classic bytecode is passively read; textual .miss/.wepn data uses a Lua recorder.
No missile controller, collision, flight, target selection or combat is simulated.
"""
import argparse
import json
import re
from pathlib import Path
from hwrm_common import PROJECT, ARCHIVE, DONOR, DONOR_SHA, save, sha
from hwrm_inspect import record_config
from lua4_data import tables as classic_tables
from audit_economy import Sources, VERSIONS, data_table

PIN = PROJECT/'baseline/missile-inputs.json'
WORK = PROJECT/'local/missile-audit'
ROOTS = ('vgr_heavymissilefrigate','vgr_destroyer','vgr_battlecruiser',
         'vgr_weaponplatform_missile','vgr_missilecorvette',
         'hgn_torpedofrigate','hgn_destroyer')
HEAVY = ('vgr_heavyfusionmissilelauncher','vgr_heavyfusionmissilelauncherweak',
         'vgr_heavyfusionmissilelauncherbc','vgr_heavyfusionmissilelauncherturret',
         'vgr_heavyfusionmissilelauncherturretleft')
ARMOURS = ('Unarmoured','Unarmoured_hw1','LightArmour','LightArmour_hw1',
           'MediumArmour','DestroyerArmour','HeavyArmour','SuperUtilityArmour',
           'ResArmour','ProbeArmour','SubSystemArmour')
WEAPON_FIELDS = ('mount','fire_type','projectile','activation','initial_speed',
    'range','radius','fire_lifetime','misc1','ejection_axis','max_effects',
    'velocity_prediction','check_line_of_fire','fire_time','burst_time','burst_wait',
    'shoot_at_secondaries','shoot_at_surroundings','azimuth_speed','declination_speed',
    'speed_when_aiming','shield_penetration','track_outside_range','wait_code_red',
    'instant_hit_threshold')


def relative(kind, ident):
    return f'{kind}/{ident.lower()}/{ident.lower()}.'+{'ship':'ship','subsystem':'subs','weapon':'wepn','missile':'miss'}[kind]


def read(sources, version, name):
    path,proof=sources.use(version,name)
    if path.read_bytes().startswith(b'\x1bLua'):
        configs,calls=classic_tables(path)
        cfg=next((configs[k] for k in ('NewShipType','NewSubSystemType') if k in configs),{})
        calls=[(c['name'],c['args'][1:]) for c in calls]
    else:
        text=path.read_text(encoding='utf-8-sig')
        for factory in ('StartMissileConfig','StartSubSystemConfig'):
            text=text.replace(factory+'()','StartShipConfig()')
        # Preserve the stock magnetic-field enum symbolically, without claiming
        # its engine numeric value. This field is outside the damage model.
        text=re.sub(r'\{\s*MagneticField\s*,','{"@engine-enum:MagneticField",',text)
        cfg,calls=record_config(text)
    result={'source':proof,'values':cfg,'calls':calls}
    try:json.dumps(result)
    except TypeError as error:
        for label,value in [('values',cfg),*[(n,a) for n,a in calls]]:
            try:json.dumps(value)
            except TypeError:raise ValueError((version,name,label,repr(value))) from error
    return result


def matching(record, name):
    return [args for fn,args in record['calls'] if fn==name]


def multipliers(args, offset):
    entries={};duplicates=[]
    for item in args[offset:]:
        assert isinstance(item,dict),item
        # HWRM permits an extra damage flag in an accuracy declaration. Preserve
        # it in the raw calls; do not interpret it as a target family or model it.
        families={k:v for k,v in item.items() if k!='damage'}
        assert len(families)==1,item
        key,value=next(iter(families.items()));key=key.lower()
        if key in entries: duplicates.append({'family':key,'values':[entries[key],value]})
        entries[key]=value
    for d in duplicates:
        entries[d['family']]=None  # Engine duplicate precedence is not assumed.
    return entries,duplicates


def weapon(record):
    starts=matching(record,'StartWeaponConfig');assert len(starts)==1
    assert len(starts[0])==len(WEAPON_FIELDS), starts
    out={'source':record['source'],'config':dict(zip(WEAPON_FIELDS,starts[0])),
         'results':matching(record,'AddWeaponResult')}
    p=matching(record,'setPenetration');a=matching(record,'setAccuracy')
    assert len(p)==1 and len(a)<=1
    out['penetration_chance']=p[0][0];out['damage_default']=p[0][1]
    out['damage_multipliers'],out['duplicate_damage_families']=multipliers(p[0],2)
    out['accuracy_default']=a[0][0] if a else None
    out['accuracy'],out['duplicate_accuracy_families']=multipliers(a[0],1) if a else ({},[])
    damage=[r for r in out['results'] if r[:3]==['Hit','DamageHealth','Target']]
    assert len(damage)<=1
    out['nominal_hit_range']={}
    if damage:
        for arm in ARMOURS:
            mult=out['damage_multipliers'].get(arm.lower(),out['damage_default'])
            out['nominal_hit_range'][arm]=[v*mult for v in damage[0][3:5]] if mult is not None else [None,None]
    out['other_calls']=[(n,a) for n,a in record['calls'] if n not in (
        'StartWeaponConfig','AddWeaponResult','setPenetration','setAccuracy')]
    return out


def catalog(sources,version):
    definitions={};edges=[];weapons={};missiles={};callbacks={}
    def visit(kind,ident):
        ident=ident.lower();name=relative(kind,ident)
        if name in definitions:return
        record=read(sources,version,name);definitions[name]=record
        if kind=='weapon':
            w=weapon(record);weapons[ident]=w
            if w['config']['fire_type']=='Missile':
                target=w['config']['projectile'].lower()
                edges.append([name,'launches',relative('missile',target)])
                visit('missile',target)
            for r in w['results']:
                if r[1]=='SpawnWeaponFire':
                    target=r[5].lower()
                    edges.append([name,'spawn_on_'+r[0].lower(),relative('weapon',target)])
                    visit('weapon',target)
        elif kind=='missile':
            missiles[ident]=record
            # A data reference, NOT proof of which weapon supplies hit damage.
            for field,child_kind in (('weaponName','weapon'),('subMunitionName','missile')):
                if record['values'].get(field):
                    target=record['values'][field].lower()
                    edges.append([name,field+'_reference',relative(child_kind,target)])
                    visit(child_kind,target)
        else:
            for fn,args in record['calls']:
                if fn in ('StartShipWeaponConfig','StartSubSystemWeaponConfig'):
                    edges.append([name,'mounted_weapon',relative('weapon',args[0])]);visit('weapon',args[0])
                elif fn=='StartShipHardPointConfig' and args[3]=='Innate' and args[5]:
                    edges.append([name,'innate_subsystem',relative('subsystem',args[5])]);visit('subsystem',args[5])
                elif fn=='addCustomCode' and args[0]:
                    script=args[0].replace('\\','/').lower().removeprefix('data:')
                    if script not in callbacks:
                        p,proof=sources.use(version,script)
                        callbacks[script]={'source':proof,'bytes':p.stat().st_size}
    for root in ROOTS:visit('ship',root)
    # All build-listed hulls, not just combat targets: find collateral armour scope.
    targets={}
    races=('hiigaran','vaygr') if version=='classic' else ('hiigaran','vaygr','kushan','taiidan')
    for race in races:
        path=f'scripts/building and research/{race}/build.lua' if version=='classic' else f'scripts/races/{race}/scripts/def_build.lua'
        rows,_=data_table(sources,version,path,'build')
        for row in rows.values():
            if row['Type']!=0:continue
            ident=row['ThingToBuild'].lower();name=relative('ship',ident)
            r=definitions.get(name) or read(sources,version,name)
            fields=('maxhealth','AttackFamily','ArmourFamily','buildBatch','SquadronSize')
            targets[ident]={'source':r['source'],'values':{k:r['values'][k] for k in fields if k in r['values']}}
    return {'weapons':weapons,'missiles':missiles,'definitions':definitions,
            'attachment_edges':sorted(edges),'callbacks':callbacks,'build_listed_hulls':targets}


def semantic_delta(before,after):
    return {k:[before.get(k),after.get(k)] for k in sorted(set(before)|set(after))
            if k!='source' and before.get(k)!=after.get(k)}


def audit(pin_inputs=False):
    assert sha(ARCHIVE)==DONOR_SHA
    sources=Sources();data={v:catalog(sources,v) for v in VERSIONS}
    inputs=json.loads(json.dumps({'schema':1,'test21_archive_sha256':DONOR_SHA,
        'layers':VERSIONS,'files':dict(sorted(sources.used.items())),
        'resolution':dict(sorted(sources.resolution.items()))}))
    if pin_inputs:
        if PIN.exists():raise RuntimeError('Input pin already exists; inspect before replacing.')
        save(PIN,inputs)
    assert PIN.exists() and json.loads(PIN.read_text(encoding='utf8'))==inputs,'Missile inputs changed.'
    w=data['test21']['weapons'];m=data['test21']['missiles']
    assert [w[n]['nominal_hit_range']['Unarmoured'][0] for n in HEAVY[:3]]==[27,27,50]
    assert [w[n]['nominal_hit_range']['LightArmour'][0] for n in HEAVY[:3]]==[270,270,500]
    assert all(w[n]['accuracy'].get('fighter')==0 and w[n]['accuracy'].get('corvette')==0 for n in HEAVY)
    assert w[HEAVY[0]]['config']['projectile']=='Vgr_MediumMissile'
    assert m['vgr_mediummissile']['values']['maxhealth']==40 and m['vgr_heavymissile']['values']['maxhealth']==90
    # Record the defects in the immutable upstream; validate fixes separately.
    assert w[HEAVY[3]]['config']['range']==6000 and w[HEAVY[4]]['config']['range']==5500
    assert w['vgr_concussionmissilelauncher']['duplicate_damage_families']==[
        {'family':'superutilityarmour','values':[0.8,0.85]}]
    deltas={kind:{} for kind in ('weapons','missiles')}
    for kind in deltas:
        before=data['pp23'][kind];after=data['test21'][kind]
        for ident in sorted(set(before)|set(after)):
            a,b=before.get(ident,{}),after.get(ident,{})
            if kind=='missiles':a=a.get('values',{});b=b.get('values',{})
            d=semantic_delta(a,b)
            if d:deltas[kind][ident]=d
    scope={arm:[ident for ident,t in data['test21']['build_listed_hulls'].items()
                if t['values'].get('ArmourFamily','').lower()==arm.lower()]
           for arm in ARMOURS[:4]}
    report={'input_files':len(sources.used),'pin_sha256':sha(PIN),'versions':data,
        'test_vs_pp23':deltas,'test21_compensation_armour_scope':scope,
        'native_engine_tested':False,'runtime_changed_by_audit':False,
        'assumptions':['nominal hit = DamageHealth range times declared armour multiplier',
            'case-normalized family lookup; no flight, collision, aiming, tactics, upgrades or fire-control model',
            'weaponName is a recorded reference; launcher vs missile hit binding is NOT established',
            'attachment graph has one config edge per mount, not a native projectile/volley count',
            'build-listed does not imply unrestricted in every MP/SP mode']}
    save(WORK/'audit.json',report)
    print(json.dumps({'report':str(WORK/'audit.json'),'input_files':len(sources.used),
        'weapons':{v:len(d['weapons']) for v,d in data.items()},'native_engine_tested':False}))
    return report


def verify_fixes(source,report=None):
    upstream=report['versions']['test21']['definitions'] if report else None
    expected={relative('weapon',HEAVY[3]):'range',
              relative('weapon','vgr_concussionmissilelauncher'):'duplicate'}
    for name,fix in expected.items():
        actual_cfg,calls=record_config((Path(source)/name).read_text(encoding='utf8'))
        if upstream:
            original_cfg=upstream[name]['values'];before=upstream[name]['calls']
        else:
            original_cfg,before=record_config((DONOR/name).read_text(encoding='utf8'))
        assert actual_cfg==original_cfg, ('Unexpected weapon field edit',name)
        # JSON normalizes tuple records to lists; compare canonical representations.
        calls=json.loads(json.dumps(calls));before=json.loads(json.dumps(before))
        for i,(fn,args) in enumerate(before):
            if fix=='range' and fn=='StartWeaponConfig':
                assert args[5]==6000;args[5]=5500
            if fix=='duplicate' and fn=='setPenetration':
                args[:]=[a for a in args if a!={'SuperUtilityArmour':0.8}]
        assert calls==before, ('Unexpected weapon edit',name)
        parsed=weapon({'source':{},'calls':calls})
        assert not parsed['duplicate_damage_families']
        if fix=='range':assert parsed['config']['range']==5500
        else:assert parsed['damage_multipliers']['superutilityarmour']==0.85
    return {'status':'passed','changed_weapons':sorted(expected),
            'all_other_config_calls_unchanged':True,'engine_tested':False}


def write_tables(report):
    lines=['# Ракетное оружие: контрольные данные','',
        'Генерируется tools/audit_missiles.py --write-tables из закреплённых входов. Числа — номинальные записи оружия, не измеренный урон, DPS или размер залпа.',
        '', 'Основной разбор и границы расчёта — [MISSILE_AUDIT.md](MISSILE_AUDIT.md).','',
        '| Пусковая | Версия | Дальность | Интервал в .wepn | Базовый урон | Unarmoured | LightArmour |',
        '|---|---|---:|---:|---:|---:|---:|']
    for ident in HEAVY:
        for version,d in report['versions'].items():
            if ident not in d['weapons']:continue
            w=d['weapons'][ident];hit=w['nominal_hit_range'];cfg=w['config']
            damage=next(r[3] for r in w['results'] if r[:3]==['Hit','DamageHealth','Target'])
            lines.append(f"| {ident} | {version} | {cfg['range']:g} | {cfg['fire_time']:g} | {damage:g} | {hit['Unarmoured'][0]:g} | {hit['LightArmour'][0]:g} |")
    lines+=['','Данные таблицы — исходный Test21 до наших двух правок. В HWMP правая пусковая платформы получает 5500 вместо 6000; её урон 950 и интервал 15 сохраняются. Дублированный коэффициент корвета сводится к одному 0.85.','',
        'Нулевая точность по Fighter/Corvette и таблица урона отвечают на разные вопросы. Значения в последних столбцах не доказывают возможность прямого огня по этим целям. Смысл weaponName при фактическом попадании требует движка.']
    (PROJECT/'docs/MISSILE_TABLES.md').write_text('\n'.join(lines).rstrip()+'\n',encoding='utf8',newline='\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pin-inputs',action='store_true');p.add_argument('--write-tables',action='store_true')
    args=p.parse_args();r=audit(args.pin_inputs)
    if args.write_tables:write_tables(r)
