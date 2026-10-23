"""Pinned Assault/Flak/platform data audit, without combat or engine simulation.

The coefficient index is explicitly incomplete: mean damage * armour * declared
accuracy / base interval, per weapon definition. It is NOT ship DPS or a TTK.
"""
import argparse
import json
import math
import re
from pathlib import Path
from hwrm_common import PROJECT, ARCHIVE, DONOR_SHA, save, sha
from hwrm_inspect import record_config
from lua4_data import Chunk, tables as classic_tables
from audit_economy import Sources, VERSIONS, data_table
from audit_progression import all_caps
from audit_missiles import read, relative, matching, weapon, semantic_delta

PIN=PROJECT/'baseline/antistrike-inputs.json'
WORK=PROJECT/'local/antistrike-audit'
ROOTS=('hgn_assaultfrigate','vgr_assaultfrigate','hgn_gunturret',
       'vgr_weaponplatform_gun','hgn_ionturret','vgr_weaponplatform_missile')
TARGETS=('hgn_interceptor','hgn_attackbomber','hgn_assaultcorvette','hgn_pulsarcorvette',
         'vgr_interceptor','vgr_bomber','vgr_missilecorvette','vgr_lasercorvette',
         'hgn_torpedofrigate','hgn_ioncannonfrigate','vgr_heavymissilefrigate')
WEAPON_CONTROLS=('hgn_attackbomber','vgr_bomber')
SELECTED_WEAPONS=('hgn_kineticburstcannon','hgn_burstcannonburst',
    'vgr_flechettecannonassaultfrigatebottom','vgr_flechettecannonassaultfrigateleft',
    'vgr_flechettecannonassaultfrigateright','hgn_vulcankineticturretlongrange',
    'vgr_vulcankineticturretlongrange','hgn_ioncannonturret',
    'vgr_heavyfusionmissilelauncherturret','vgr_heavyfusionmissilelauncherturretleft')
HULL_FIELDS=('maxhealth','regentime','minRegenTime','buildCost','buildTime','mainEngineMaxSpeed',
    'thrusterMaxSpeed','rotationMaxSpeed','mainEngineAccelTime','mainEngineBrakeTime',
    'thrusterAccelTime','thrusterBrakeTime','rotationAccelTime','rotationBrakeTime',
    'accelerationAngle','goalReachEpsilon','slideMoveRange','thrusterUsage','maxBankingAmount',
    'useEngagementRanges','sideArmourDamage','rearArmourDamage','ArmourFamily','AttackFamily',
    'UnitCapsFamily','UnitCapsShipType','defaultStance','defaultROE','prmSensorRange',
    'secSensorRange','buildBatch','SquadronSize','DisplayFamily','BuildFamily')
STYLE_FIELDS=('inRangeMultiplier','happilySameHeight','tooLongOutOfRange',
    'moveAttackMaxDistanceMultiplier','facingAngle','facingangle','tryToFaceTarget',
    'maxTimeToSpendTryingToMatchHeight','flyToTargetBecauseItsFarOutOfRangeDelay',
    'flyToSameHeightAsTargetDelay','flyToAboveTheTargetDelay','faceTargetHorizontal',
    'faceTargetVertical')
MODIFIERS=('setBallistics','setAccuracyFalloff','setDamageFalloff','setSpeedvsAccuracyAgainst',
           'setMissileKiller','setMissProperties','setLifetimeMult','setMiscValues',
           'setRangeBoost','setRangeByStance','setFireMultFactor','setAngles')


def attack_style(sources,version,name):
    rel='scripts/attack/'+name.lower()+'.lua'
    if rel not in sources.effective(version):
        return {'name':name,'resolved':False}
    p,proof=sources.use(version,rel)
    if p.read_bytes().startswith(b'\x1bLua'):
        if Chunk(p).proto['children']:
            return {'name':name,'source':proof,'resolved':True,'declared_numeric_fields':{},
                    'data_not_evaluated':'Classic attack script contains function prototypes',
                    'engine_attack_style_not_simulated':True}
        values,calls=classic_tables(p);assert not calls,rel
        data=values['Data'];fields={k:data[k] for k in STYLE_FIELDS if k in data}
    else:
        text=p.read_text(encoding='utf-8-sig');fields={}
        for key in STYLE_FIELDS:
            values=re.findall(r'^\s*'+re.escape(key)+r'\s*=\s*(-?\d+(?:\.\d*)?)\s*,',text,re.M)
            assert len(values)<=1,(rel,key)
            if values:fields[key]=float(values[0])
    return {'name':name,'source':proof,'resolved':True,'declared_numeric_fields':fields,
            'engine_attack_style_not_simulated':True}


def collect(sources,version):
    definitions={};weapons={};edges=[];styles={};hulls={}
    def visit(kind,ident):
        ident=ident.lower();rel=relative(kind,ident)
        if rel in definitions:return
        r=read(sources,version,rel);definitions[rel]=r
        if kind=='weapon':
            w=weapon(r);weapons[ident]=w
            w['modifiers']={n:matching(r,n) for n in MODIFIERS if matching(r,n)}
            if w['config']['fire_type']=='Missile':
                child=w['config']['projectile'];edges.append([rel,'launches',relative('missile',child)]);visit('missile',child)
            for result in w['results']:
                if result[1]=='SpawnWeaponFire':
                    child=result[5];edges.append([rel,'spawn_on_'+result[0].lower(),relative('weapon',child)]);visit('weapon',child)
        elif kind=='missile':
            # Record common weaponName references, not assumed damage binding.
            for key,child_kind in (('weaponName','weapon'),('subMunitionName','missile')):
                if r['values'].get(key):
                    child=r['values'][key];edges.append([rel,key+'_reference',relative(child_kind,child)]);visit(child_kind,child)
        else:
            for fn,args in r['calls']:
                if fn in ('StartShipWeaponConfig','StartSubSystemWeaponConfig'):
                    edges.append([rel,'mounted_weapon',relative('weapon',args[0])]);visit('weapon',args[0])
                elif fn=='StartShipHardPointConfig' and args[3]=='Innate' and args[5]:
                    edges.append([rel,'innate_subsystem',relative('subsystem',args[5])]);visit('subsystem',args[5])
    for ident in ROOTS+WEAPON_CONTROLS:visit('ship',ident)
    for ident in ('hgn_mine','vgr_mine'):visit('missile',ident)
    for ident in ROOTS+TARGETS:
        r=definitions.get(relative('ship',ident)) or read(sources,version,relative('ship',ident))
        hulls[ident]={'source':r['source'],'fields':{k:r['values'][k] for k in HULL_FIELDS if k in r['values']},
            'abilities':matching(r,'addAbility'),'supply':matching(r,'setSupplyValue'),
            'tactics':matching(r,'setTacticsMults'),'target_speed_modifiers':matching(r,'setSpeedvsAccuracyApplied')}
        if ident in ROOTS:
            attack=[a for a in matching(r,'addAbility') if a[0]=='CanAttack'];assert len(attack)==1
            names=[attack[0][8],*[v for table in attack[0][9:] for v in table.values()]]
            for name in names:
                if name.lower() not in styles:styles[name.lower()]=attack_style(sources,version,name)
    caps={race:all_caps(sources,version,race) for race in ('hiigaran','vaygr')}
    research={}
    for race in caps:
        rel=f'scripts/building and research/{race}/research.lua' if version=='classic' else f'scripts/races/{race}/scripts/def_research.lua'
        rows,_=data_table(sources,version,rel,'research',True)
        research[race]={r['Name']:r for r in rows.values() if any(
            token in (r.get('TargetName','')+' '+r['Name']).lower()
            for token in ('assaultfrigate','platform','gunturret','ionturret','frigatehealth','frigatespeed'))
            or (r.get('UpgradeName')=='MAXSPEED' and r.get('Cost',0)>0
                and r.get('TargetName','').lower() in ('hgn_interceptor','fighter'))}
    return {'hulls':hulls,'weapons':weapons,'definitions':definitions,'attachment_edges':sorted(edges),
            'attack_styles':styles,'caps':caps,'relevant_research':research}


def coefficient_index(w,attack_family,armour_family):
    """Comparable arithmetic only for single direct damage, ignoring modifiers."""
    r=[r for r in w['results'] if r[:3]==['Hit','DamageHealth','Target']]
    cfg=w['config']
    if len(r)!=1 or cfg['fire_type'] not in ('Bullet','InstantHit') or cfg['fire_time']<=0:
        return None
    if cfg['fire_lifetime'] or cfg['burst_time'] or cfg['burst_wait']:
        return None  # No invented beam/burst event or shot counts.
    accuracy=w['accuracy'].get(attack_family.lower(),w['accuracy_default'])
    armour=w['damage_multipliers'].get(armour_family.lower(),w['damage_default'])
    if accuracy is None or armour is None:return None
    return ((r[0][3]+r[0][4])/2)*armour*accuracy/cfg['fire_time']


def checks(data):
    t=data['test21'];w=t['weapons'];h=t['hulls']
    guns=[w[n] for n in SELECTED_WEAPONS[2:5]]
    normalized=[{k:v for k,v in g.items() if k not in ('source','other_calls','modifiers')} for g in guns]
    assert normalized[0]==normalized[1]==normalized[2]
    # Three cannon variants differ only in their declared angles.
    others=[[row for row in g['other_calls'] if row[0]!='setAngles'] for g in guns]
    assert others[0]==others[1]==others[2]
    for ident in SELECTED_WEAPONS[2:7]:
        m=w[ident]['modifiers'];assert m['setBallistics']==[[1,0]]
        assert 'setAccuracyFalloff' not in m and m['setMissileKiller']==[[1]]
        assert 'setSpeedvsAccuracyAgainst' in m
    assert all('setDamageFalloff' in g['modifiers'] for g in guns)
    assert all('setDamageFalloff' not in w[n]['modifiers'] for n in SELECTED_WEAPONS[5:7])
    assert w['hgn_kineticburstcannon']['nominal_hit_range']=={}
    spawn=w['hgn_kineticburstcannon']['results']
    assert spawn==[['Hit','SpawnWeaponFire','Target',0,0,'Hgn_BurstCannonBurst'],
                  ['Miss','SpawnWeaponFire','Target',0,0,'Hgn_BurstCannonBurst']]
    assert w['hgn_burstcannonburst']['config']['radius']==60
    assert w['hgn_burstcannonburst']['config']['max_effects']==10  # NOT ten confirmed damage applications.
    assert h['hgn_assaultfrigate']['fields']['maxhealth']==h['vgr_assaultfrigate']['fields']['maxhealth']==20000
    assert math.isclose(coefficient_index(guns[0],'Fighter','Unarmoured'),95*0.5*0.4/1.5)
    return {'turret_variants_equal_except_angles':True,'flak_hit_and_miss_share_burst':True,
            'retained_speed_modifiers_recorded':True,'coefficient_model_not_combat':True}


def escape_speed_reference(data):
    out={}
    for ident,race,target in (('hgn_interceptor','hiigaran','hgn_interceptor'),('vgr_interceptor','vaygr','fighter')):
        h=data['hulls'][ident]
        rows=[r for r in data['relevant_research'][race].values() if r.get('UpgradeName')=='MAXSPEED'
              and r.get('Cost',0)>0 and r.get('TargetName','').lower()==target]
        assert len(rows)==1,(ident,rows)
        speed_stances=[r for r in h['tactics'] if r[0]=='MAXSPEED'];assert len(speed_stances)==1
        base=h['fields']['mainEngineMaxSpeed'];upgrade=rows[0]['UpgradeValue'];evasive=speed_stances[0][2]
        out[ident]={'base':base,'research':rows[0]['Name'],'upgrade':upgrade,'evasive_multiplier':evasive,
                    'nominal_upgraded_neutral':base*upgrade,'nominal_upgraded_evasive':base*upgrade*evasive,
                    'arithmetic_only_not_measured_speed':True}
    return out


def audit(pin_inputs=False):
    assert sha(ARCHIVE)==DONOR_SHA
    sources=Sources();data={v:collect(sources,v) for v in VERSIONS}
    assertions=checks(data)
    pin=json.loads(json.dumps({'schema':1,'test21_archive_sha256':DONOR_SHA,'layers':VERSIONS,
        'files':dict(sorted(sources.used.items())),'resolution':dict(sorted(sources.resolution.items()))}))
    if pin_inputs:
        if PIN.exists():raise RuntimeError('Input pin exists; inspect before replacement.')
        save(PIN,pin)
    assert PIN.exists() and json.loads(PIN.read_text(encoding='utf8'))==pin,'Antistrike inputs changed.'
    indices={v:{ident:{target:coefficient_index(d['weapons'][ident],t['fields']['AttackFamily'],t['fields']['ArmourFamily'])
                      for target,t in d['hulls'].items() if target in TARGETS}
                for ident in SELECTED_WEAPONS if ident in d['weapons']} for v,d in data.items()}
    changes={}
    for kind in ('hulls','weapons','attack_styles','caps','relevant_research'):
        a,b=data['pp23'][kind],data['test21'][kind]
        changes[kind]={k:semantic_delta(a.get(k,{}),b.get(k,{})) for k in sorted(set(a)|set(b))
                       if semantic_delta(a.get(k,{}),b.get(k,{}))}
    report={'input_files':len(sources.used),'pin_sha256':sha(PIN),'versions':data,
        'test_vs_pp23':changes,'per_weapon_coefficient_indices':indices,'source_checks':assertions,
        'test21_escape_speed_reference':escape_speed_reference(data['test21']),
        'native_engine_tested':False,'runtime_changed':False,
        'limitations':['index ignores falloff, speed, geometry, tactics, upgrades, physical hits and event counts',
            'index is per weapon definition; no HOD fire-point or actual projectile count inferred',
            'Flak burst radius/effects do not specify actual victims or total damage applications',
            'attack-style numeric declarations are data, not an AI/pursuit simulation',
            'four versions are original inputs; prepared HWMP retains the two prior missile fixes']}
    save(WORK/'audit.json',report)
    print(json.dumps({'input_files':len(sources.used),'weapons':{v:len(d['weapons']) for v,d in data.items()},
                      'source_checks':assertions,'runtime_changed':False,'native_engine_tested':False}))
    return report


def prepare_experiments(report):
    """Write isolated, uninstalled text overlays; no runnable mod or game launch."""
    sources=Sources();out=WORK/'experiments';manifest={}
    groups={'assault-accuracy-falloff':SELECTED_WEAPONS[2:5],
            'platform-accuracy-falloff':SELECTED_WEAPONS[5:7],
            'assault-flat-speed-curve':SELECTED_WEAPONS[2:5]}
    for group,names in groups.items():
        files={}
        for ident in names:
            rel=relative('weapon',ident);path,proof=sources.use('test21',rel)
            assert proof==report['versions']['test21']['definitions'][rel]['source']
            text=path.read_text(encoding='utf-8-sig');cfg,before=record_config(text)
            if group.endswith('accuracy-falloff'):
                original=report['versions']['pp23']['weapons'][ident]['modifiers']['setAccuracyFalloff']
                assert len(original)==1 and len(original[0])==2
                assert not [a for n,a in before if n=='setAccuracyFalloff']
                line='setAccuracyFalloff(NewWeaponType, '+', '.join(repr(x) for x in original[0])+');'
                text=text.rstrip()+'\n'+line+'\n'
            else:
                rows=matching({'calls':before},'setSpeedvsAccuracyAgainst');assert len(rows)==1
                values=list(rows[0]);assert values[0]==1 and len(values)==11
                for i in range(2,len(values),2):values[i]=1.0
                line='setSpeedvsAccuracyAgainst(NewWeaponType, '+', '.join(repr(x) for x in values)+');'
                pattern=r'^setSpeedvsAccuracyAgainst\([^\n]+\);'
                text,count=re.subn(pattern,lambda _:line,text,count=1,flags=re.M);assert count==1
            after_cfg,after=record_config(text);assert cfg==after_cfg
            changed='setAccuracyFalloff' if group.endswith('accuracy-falloff') else 'setSpeedvsAccuracyAgainst'
            assert [(n,a) for n,a in before if n!=changed]==[(n,a) for n,a in after if n!=changed]
            assert len([n for n,a in after if n==changed])==1
            target=(out/group/rel).resolve();assert target.is_relative_to(out.resolve())
            target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='ascii',newline='\n')
            files[rel]={'original':proof,'experiment_sha256':sha(target),'only_changed_call':changed}
        manifest[group]={'files':files,'packaged':False,'installed':False,'engine_tested':False}
    save(out/'manifest.json',{'variants':manifest,'native_launch_required_for_results':True})
    return {'variants':len(groups),'weapon_overlays':sum(len(v['files']) for v in manifest.values()),
            'packaged':False,'installed':False,'engine_tested':False}


def write_tables(report):
    lines=['# Assault/Flak/платформы: исходные контрольные данные','',
        'Генерируется tools/audit_antistrike.py --write-tables. Показаны оригинальные входы Classic/HWRM/PP/Test; подготовленный HWMP дополнительно исправляет правую ракетную пусковую до5500.','',
        'Анализ и ограничения — [ANTISTRIKE_AUDIT.md](ANTISTRIKE_AUDIT.md).','',
        '| Корпус | Версия | RU | Базовые с | HP | Скорость | Разгон | Поворот |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for ident in ROOTS:
        for v,d in report['versions'].items():
            f=d['hulls'][ident]['fields']
            vals=[f[k] for k in ('buildCost','buildTime','maxhealth','mainEngineMaxSpeed','mainEngineAccelTime','rotationMaxSpeed')]
            lines.append('| '+ident+' | '+v+' | '+' | '.join(f'{x:g}' for x in vals)+' |')
    lines+=['','## Коэффициентный индекс одиночной пушки','',
        'Индекс = средний DamageHealth × объявленный множитель брони × объявленная точность / базовый интервал. **Это не DPS корабля и не TTK:** отсутствуют дистанция, скорость, стойки, наука, геометрия, число событий и физические попадания. По Flak/лучам/очередям значение не выдумывается. Старую баллистику нельзя сравнивать с процентной моделью как прямой рост/падение DPS.','',
        '| Пушка | Версия | Hgn Interceptor | Hgn Pulsar | Vgr Missile Corvette | Hgn Torpedo Frigate |',
        '|---|---|---:|---:|---:|---:|']
    selected=(SELECTED_WEAPONS[3],*SELECTED_WEAPONS[5:7])
    for ident in selected:
        for v,rows in report['per_weapon_coefficient_indices'].items():
            if ident not in rows:continue
            vals=[rows[ident][t] for t in ('hgn_interceptor','hgn_pulsarcorvette','vgr_missilecorvette','hgn_torpedofrigate')]
            lines.append('| '+ident+' | '+v+' | '+' | '.join('—' if n is None else f'{n:.4g}' for n in vals)+' |')
    (PROJECT/'docs/ANTISTRIKE_TABLES.md').write_text('\n'.join(lines).rstrip()+'\n',encoding='utf8',newline='\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pin-inputs',action='store_true');p.add_argument('--write-tables',action='store_true')
    p.add_argument('--prepare-experiments',action='store_true')
    a=p.parse_args();r=audit(a.pin_inputs)
    if a.write_tables:write_tables(r)
    if a.prepare_experiments:print(json.dumps(prepare_experiments(r)))
