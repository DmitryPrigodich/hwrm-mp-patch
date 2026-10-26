"""Isolated native automatic test worlds. Build/install never launches a game."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
from hwrm_common import PROJECT,CACHE,GAME,DONOR,index,sha,save,build_directory
from hwrm_archive import package_source
from install_hwmp24 import active_processes,other_mod_files

ROOT=PROJECT/'autotests'
WORK=PROJECT/'local/auto-tests'
RELEASE=PROJECT/'local/HWMPAutoTests-release'
BUILD=build_directory('native-auto-tests',PROJECT)
SOURCE=BUILD/'source'
IDENTITY='HWMP-native-auto-tests-v1'
CAMPAIGN='HWMPAutoTests'
MODES=('Mechanics','Antistrike','Economy6','Economy7','SaveLoad','SpeedCurve','Progression','EconomyMatrix6','EconomyMatrix7','GravityScope','SaveLoadAuto','SaveLoadTrace','Defense','DefenseIdentity','DefenseOrders','DefenseIntercept','Transport','Salvage','DockStall','SalvageBaselines','ResearchEffects','GravityToggle','GravityExpiry','HW1Damage','EconomyRaids','PaidProduction','EconomyRecovery','Mines','CombatGeometry')

def lua(v):
    if isinstance(v,str):return json.dumps(v,ensure_ascii=True)
    if isinstance(v,(int,float)):return str(v)
    if isinstance(v,list):return '{'+','.join('['+str(i)+']='+lua(x) for i,x in enumerate(v,1))+'}'
    if isinstance(v,dict):return '{'+','.join(k+'='+lua(x) for k,x in v.items())+'}'
    raise TypeError(v)

def put(n,t):
    p=SOURCE/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t+'\n',encoding='ascii',newline='\n')

def prepare():
    base=Path(json.loads((PROJECT/'local/hwmp-patch-2.4/manifest.json').read_text(encoding='utf8'))['source'])
    base_hashes={n:sha(p) for n,p in index(base).items()}
    assert 'scripts/weaponfire/vgr_mediummissile/vgr_mediummissile.wf' in base_hashes
    if SOURCE.exists():
        assert SOURCE.resolve().parent==BUILD.resolve() and (BUILD/'owner.txt').read_text()==IDENTITY
        shutil.rmtree(SOURCE)
    (BUILD/'owner.txt').write_text(IDENTITY)
    shutil.copytree(base,SOURCE)
    native={}
    for folder in ('rm-base','rm-hw1','rm-hw2','rm-mp','test'):
        native.update(index(CACHE/'players-patch-audit'/folder))
    native.update(index(base))
    alterations={}
    diagnostic_overrides={}
    def clone_ship(original,name,transform):
        src=native[f'ship/{original}/{original}.ship'];old=src.read_text(encoding='utf-8-sig');new=transform(old)
        # A private transform must never silently consume structural ship fields.
        for field in ('CollisionFamily','BuildFamily','DockFamily','AttackFamily'):
            if re.search(r'NewShipType\.'+field+r'\s*=',old):
                assert re.search(r'NewShipType\.'+field+r'\s*=',new),(name,field)
        put(f'ship/{name}/{name}.ship',new)
        for ext in ('.hod','.events'):
            key=f'ship/{original}/{original}{ext}'
            assert key in native,key
            dst=SOURCE/f'ship/{name}/{name}{ext}';shutil.copy2(native[key],dst)
        alterations[name]={'template':original,'source_sha256':sha(src),'generated_sha256':sha(SOURCE/f'ship/{name}/{name}.ship')}
    def strip_weapons(text):
        text=re.sub(r'^StartShipWeaponConfig\([^\n]+\);?\s*$', '',text,flags=re.M)
        return re.sub(r'^StartShipHardPointConfig\([^\n]*,"Weapon",[^\n]+\);?\s*$', '',text,flags=re.M)
    for tag,armour,attack in [('medium','MediumArmour','Frigate'),('heavy','HeavyArmour','Frigate'),('light','LightArmour','Corvette'),('unarmoured','Unarmoured','Fighter')]:
        def probe(text,armour=armour,attack=attack):
            text=strip_weapons(text)
            text=re.sub(r'^NewShipType.maxhealth=.*$', 'NewShipType.maxhealth=100000',text,flags=re.M)
            text=re.sub(r'^NewShipType.(?:regentime|minRegenTime)=.*$',lambda m:m[0].split('=')[0]+'=0',text,flags=re.M)
            text=re.sub(r'^NewShipType.ArmourFamily=.*$', 'NewShipType.ArmourFamily="'+armour+'"',text,flags=re.M)
            return re.sub(r'^NewShipType.AttackFamily=.*$', 'NewShipType.AttackFamily="'+attack+'"',text,flags=re.M)
        clone_ship('hgn_torpedofrigate','hwa_probe_'+tag,probe)
    launchers=[('hmf','vgr_heavymissilefrigate','Vgr_HeavyFusionMissileLauncher'),('dd','vgr_destroyer','Vgr_HeavyFusionMissileLauncherWeak'),('bc','vgr_battlecruiser','Vgr_HeavyFusionMissileLauncherBC')]
    for tag,ship,weapon in launchers:
        wname='hwa_single_'+tag
        wpath=native[f'weapon/{weapon.lower()}/{weapon.lower()}.wepn'];text=wpath.read_text(encoding='utf-8-sig')
        m=re.search(r'StartWeaponConfig\(([^;]+)\);',text);assert m
        args=m[1].split(',');assert len(args)==26
        args[14]='9999';args[15]='0';args[16]='0';args[17]='0';args[18]='0'
        text=text[:m.start(1)]+','.join(args)+text[m.end(1):]
        put(f'weapon/{wname}/{wname}.wepn',text)
        def launcher(text,weapon=weapon,wname=wname):
            lines=re.findall(r'^StartShipWeaponConfig\([^\n]+\);?\s*$',text,re.M)
            keep=[x for x in lines if '"'+weapon+'"' in x]
            if weapon=='Vgr_HeavyFusionMissileLauncherBC':
                keep=['StartShipWeaponConfig(NewShipType,"Vgr_HeavyFusionMissileLauncherBC","Weapon_MissileBattery","");']
            assert len(keep)==1,(ship,keep)
            return strip_weapons(text)+'\n'+keep[0].replace('"'+weapon+'"','"'+wname+'"')+'\n'
        clone_ship(ship,'hwa_launcher_'+tag,launcher)
    for variant in ('control','flat','cap'):
        def assault(text,variant=variant):
            changed=0
            # The three cannons are native innate weapon subsystems.
            weapons=sorted(set(re.findall(r'"(Vgr_FlechetteCannonAssaultFrigate[^\"]+)"',text)))
            for weapon in weapons:
                # Keep the pinned Test21 control even after the main patch adopts the cap.
                old=(DONOR/f'weapon/{weapon.lower()}/{weapon.lower()}.wepn').read_text(encoding='utf-8-sig')
                m=re.search(r'setSpeedvsAccuracyAgainst\(NewWeaponType,([^;]+)\);',old)
                if not m:continue
                changed+=1
                parts=m[1].split(',');assert len(parts)==11
                if variant=='flat':
                    for i in (2,4,6,8,10):parts[i]='1'
                elif variant=='cap':parts[10]='1.2'
                new=old[:m.start(1)]+','.join(parts)+old[m.end(1):]
                w='hwa_'+variant+'_'+weapon.lower();put(f'weapon/{w}/{w}.wepn',new)
                sub='hwa_'+variant+'_sub_'+weapon.lower()
                subkey=f'subsystem/{weapon.lower()}/{weapon.lower()}'
                original_sub=native[subkey+'.subs'].read_text(encoding='ascii')
                put(f'subsystem/{sub}/{sub}.subs',original_sub.replace('"'+weapon+'"','"'+w+'"'))
                for ext in ('.hod','.events'):
                    if subkey+ext in native:
                        shutil.copy2(native[subkey+ext],SOURCE/f'subsystem/{sub}/{sub}{ext}')
                    elif ext=='.hod':assert 'LoadShared' in original_sub,subkey
                text=text.replace('"'+weapon+'"','"'+sub+'"')
            assert changed==3,changed
            return text
        clone_ship('vgr_assaultfrigate','hwa_assault_'+variant,assault)
    for tag,speed in [('base',348),('upgraded',487.2),('fast',535.92)]:
        def speed_probe(text,speed=speed):
            text=strip_weapons(text)
            for attr,value in [('maxhealth',100000),('regentime',0),('minRegenTime',0),('thrusterMaxSpeed',speed),('mainEngineMaxSpeed',speed)]:
                text,n=re.subn(r'^NewShipType\.'+attr+r'\s*=.*$',f'NewShipType.{attr}={value}',text,flags=re.M)
                if attr!='minRegenTime':assert n==1,(attr,n)
            return text
        clone_ship('hgn_interceptor','hwa_speed_'+tag,speed_probe)
    trace='''dofilepath("data:scripts/hwmp24/autotests/run.lua")
function HWA_TraceShip(event,group,player,id)
    local count=-1
    if type(HWMP_EffectRecords)=="table" then count=getn(HWMP_EffectRecords) end
    print("HWMP_SHIP|run="..HWA_RUN.."|t="..Universe_GameTime().."|event="..event.."|ship_id="..id.."|group="..group.."|records="..count.."|serial="..(HWMP_EffectSerial or -1))
    if count>0 and event~="update" then
        for i=1,count do
            local r=HWMP_EffectRecords[i]
            local speed=-1
            if r.speed then speed=r.speed.baseline end
            local owners=""
            if r.speed then
                local key=next(r.speed.owners,nil)
                while key do owners=owners..key..",";key=next(r.speed.owners,key) end
            end
            print("HWMP_SHIP_RECORD|run="..HWA_RUN.."|t="..Universe_GameTime().."|event="..event.."|ship_id="..id.."|record="..i.."|target="..r.group.."|entries="..SobGroup_Count(r.group).."|speed_baseline="..speed.."|owners="..owners)
        end
    end
end
'''
    for race in ('kus','tai'):
        original=race+'_gravwellgenerator';private='hwa_trace_'+original
        path=f'ship/{private}/{private}.lua'
        mapping={prefix+'_'+race.capitalize()+'_GravWellGenerator':'HWA_'+prefix+'_'+race+'_GW' for prefix in ('Start','Do','Finish','Create','Update','Destroy')}
        body='dofilepath("data:ship/'+original+'/'+original+'.lua")\n'+trace
        for old,new in mapping.items():
            event=old.split('_')[0].lower()
            body+=f'function {new}(g,p,id)\n HWA_TraceShip("{event}_before",g,p,id)\n {old}(g,p,id)\n HWA_TraceShip("{event}_after",g,p,id)\nend\n'
        put(path,body)
        def wrap(text,original=original,path=path,mapping=mapping):
            text,n=re.subn(r'data:ship/'+original+'/'+original+r'\.lua','data:'+path,text,flags=re.I)
            assert n>=2,(original,n)
            for old,new in mapping.items():text=text.replace('"'+old+'"','"'+new+'"')
            return text
        clone_ship(original,private,wrap)
    # Diagnostic UI adapter only; all gameplay files remain byte-identical.
    ui='ui/newui/uisettings.lua'
    before=(SOURCE/ui).read_text(encoding='ascii')
    screen_count=len(re.findall(r'(?m)^\s*name\s*=',before.split('GameScreens = {',1)[1]))
    assert screen_count>10
    after=before+'\nGameScreens['+str(screen_count+1)+']={name="HWMPAutoReload",filename="data:ui/newui/hwmpautoreload.lua",activated=0}\n'
    put(ui,after)
    diagnostic_overrides[ui]={'before':base_hashes[ui],'after':sha(SOURCE/ui),'purpose':'register inactive screen for loading only an owned test checkpoint'}
    callback="if not HWMPReloadAttempted then HWMPReloadAttempted=1; LoadGame('player:Campaign/HWMPAUTOTESTS/HWMPAutoCheckpoint.sav') end"
    put('ui/newui/hwmpautoreload.lua','HWMPAutoReload={stylesheet="HW2StyleSheet",RootElementSettings={Layout={size_WH={w=1,h=1,wr="scr",hr="scr"}}},giveParentMouseInput=1,eventOpaque=0,pixelUVCoords=1,onShow='+lua(callback)+'}')
    put('scripts/hwmp24/autotests/runtime.lua',(ROOT/'runtime.lua').read_text(encoding='ascii'))
    from auto_defense import prepare as prepare_defense,cases as defense_cases
    prepare_defense(put,clone_ship,native,DONOR)
    put('scripts/hwmp24/autotests/defense.lua',(ROOT/'defense.lua').read_text(encoding='ascii'))
    from auto_economy_recovery import cases as recovery_cases
    from auto_mines import prepare as prepare_mines,cases as mine_cases
    from auto_combat_geometry import prepare as prepare_geometry,cases as geometry_cases
    prepare_mines(put,clone_ship,native,SOURCE)
    prepare_geometry(put,clone_ship,native)
    for module in ('economy_recovery','mines'):
        put('scripts/hwmp24/autotests/'+module+'.lua',(ROOT/(module+'.lua')).read_text(encoding='ascii'))
    from auto_production import cases as production_cases
    put('scripts/hwmp24/autotests/production.lua',(ROOT/'production.lua').read_text(encoding='ascii'))
    from auto_gravity_lifecycle import cases as lifecycle_cases
    from auto_hw1_damage import prepare as prepare_hw1_damage,cases as hw1_damage_cases
    from auto_economy_raids import cases as raids_cases
    prepare_hw1_damage(put,clone_ship,native)
    for module in ('gravity_lifecycle','hw1_damage','economy_raids'):
        put('scripts/hwmp24/autotests/'+module+'.lua',(ROOT/(module+'.lua')).read_text(encoding='ascii'))
    from auto_effects import cases as effect_cases
    put('scripts/hwmp24/autotests/research_effects.lua',(ROOT/'research_effects.lua').read_text(encoding='ascii'))
    from auto_dock import prepare as prepare_dock,cases as dock_cases
    prepare_dock(put,clone_ship,native)
    put('scripts/hwmp24/autotests/dock.lua',(ROOT/'dock.lua').read_text(encoding='ascii'))
    from auto_salvage import prepare as prepare_salvage,cases as salvage_cases
    prepare_salvage(put,clone_ship,native)
    put('scripts/hwmp24/autotests/salvage.lua',(ROOT/'salvage.lua').read_text(encoding='ascii'))
    from auto_transport import cases as transport_cases
    put('scripts/hwmp24/autotests/transport.lua',(ROOT/'transport.lua').read_text(encoding='ascii'))
    plans={};fixtures={};generated=[]
    for mode in MODES:
        ships=[];volumes=[];asteroids=[];cases=[]
        def add(name,kind,pos,owner,size=1):ships.append([name,kind,list(pos),owner,size]);return name
        if not mode.startswith('EconomyMatrix') and mode not in ('EconomyRaids','EconomyRecovery'):
            add('HWA_MotherH','hgn_mothership',[-80000,0,-80000],0)
            add('HWA_MotherV','vgr_mothership',[80000,0,-80000],1)
        if mode=='Transport':cases=transport_cases(add,volumes)
        if mode in ('Salvage','SalvageBaselines'):cases=salvage_cases(add,volumes,mode)
        if mode=='ResearchEffects':cases=effect_cases(add,volumes)
        if mode in ('GravityToggle','GravityExpiry'):cases=lifecycle_cases(add,volumes,mode)
        if mode=='HW1Damage':cases=hw1_damage_cases(add,volumes)
        if mode=='PaidProduction':cases=production_cases(add,volumes)
        if mode=='EconomyRecovery':cases=recovery_cases(add,volumes,asteroids)
        if mode=='Mines':cases=mine_cases(add,volumes)
        if mode=='CombatGeometry':cases=geometry_cases(add,volumes)
        if mode=='EconomyRaids':cases=raids_cases(add,volumes,asteroids)
        if mode=='DockStall':cases=dock_cases(add,volumes)
        if mode=='Mechanics':
            for j,race in enumerate(('kus','tai','kus','tai')):
                x=-70000+j*18000;z=-10000;prefix='gw_'+race
                if j>=2:prefix+='_reverse'
                owner=4+(j%2)
                a=add(prefix+'_a',race+'_gravwellgenerator',[x-500,0,z],owner)
                b=add(prefix+'_b',race+'_gravwellgenerator',[x+500,0,z],owner)
                t=add(prefix+'_target',race+'_interceptor',[x,0,z+1200],owner)
                q=add(prefix+'_enemy','hgn_interceptor',[x,0,z+1700],0,0)
                if j>=2:a,b=b,a
                cases.append({'id':prefix,'kind':'gravity','a':a,'b':b,'target':t,'enemy':q,'x':x,'z':z})
            for owner,race,x in [(0,'hgn',-30000),(1,'vgr',0)]:
                c='dock_'+race
                carrier=add(c+'_carrier',race+'_carrier',[x,0,-60000],owner)
                target=add(c+'_target',race+'_interceptor',[x,0,-58000],owner,0)
                cases.append({'id':c,'kind':'dock','target':target,'carrier':carrier,'player':owner,'x':x,'z':-60000})
            for j,distance in enumerate((5800,5300)):
                x=-55000+j*35000;z=-35000;c='platform_range_'+str(distance)
                source=add(c+'_s','vgr_weaponplatform_missile',[x,0,z],1)
                target=add(c+'_t','hwa_probe_medium',[x,0,z+distance],0)
                cases.append({'id':c,'kind':'platform_range','source':source,'target':target,'distance':distance,'x':x,'z':z})
            k=0
            for rep in range(1,4):
                for tag,ship,weapon in launchers:
                    for action,armour in [('direct','medium'),('direct','heavy'),('retarget','unarmoured'),('retarget','light')]:
                        x=-90000+(k%10)*18000;z=12000+(k//10)*18000;k+=1
                        c=f'{tag}_{action}_{armour}_r{rep}'
                        src=add(c+'_s','hwa_launcher_'+tag,[x,0,z],1)
                        primary=add(c+'_p','hwa_probe_'+(armour if action=='direct' else 'medium'),[x,0,z+2200],0)
                        replacement=add(c+'_r','hwa_probe_'+armour,[x+700,0,z+2200],0)
                        cases.append({'id':c,'kind':'missile','action':action,'armour':armour,'launcher':tag,'volley':{'hmf':2,'dd':4,'bc':1}[tag],'source':src,'target':primary,'replacement':replacement,'x':x,'z':z})
            for armour in ('unarmoured','light'):
                x=100000;z=10000+(0 if armour=='light' else 18000);c='death_control_'+armour
                primary=add(c+'_p','hwa_probe_medium',[x,0,z+2200],0)
                replacement=add(c+'_r','hwa_probe_'+armour,[x+700,0,z+2200],0)
                cases.append({'id':c,'kind':'death_control','target':primary,'replacement':replacement,'x':x,'z':z})
            for j,(ship,owner,tech,mult) in enumerate([('hgn_gunturret',2,'GunTurretHealthUpgrade1',1.5),('hgn_ionturret',2,'IonTurretHealthUpgrade1',1.5),('vgr_weaponplatform_gun',3,'PlatformHealthUpgrade1',1.75),('vgr_weaponplatform_missile',3,'PlatformHealthUpgrade1',1.75)]):
                g=add('hp_'+str(j),ship,[-60000+j*12000,0,-40000],owner)
                cases.append({'id':'hp_'+str(j),'kind':'research_hp','target':g,'player':owner,'tech':tech,'expected':mult})
        if mode in ('Defense','DefenseIdentity','DefenseOrders','DefenseIntercept'):cases=defense_cases(add,mode)
        if mode=='Antistrike':
            k=0
            for rep in range(1,4):
                for shooter in ('control','flat','applied','flak'):
                    for upgrade in (0,1):
                        for stance in (1,2):
                            x=-100000+(k%12)*18000;z=(k//12)*23000;k+=1
                            c=f'aa_{shooter}_u{upgrade}_s{stance}_r{rep}';isflak=shooter=='flak'
                            source=add(c+'_s','hgn_assaultfrigate' if isflak else 'vgr_assaultfrigate' if shooter=='applied' else 'hwa_assault_'+shooter,[x+1000,0,z],0 if isflak else 1)
                            owner=(3 if upgrade else 1) if isflak else (2 if upgrade else 0)
                            target=add(c+'_t','vgr_interceptor' if isflak else 'hgn_interceptor',[x,0,z-9000],owner,0)
                            volume=c+'_end';volumes.append([volume,[x,0,z+17000],100])
                            cases.append({'id':c,'kind':'pass','source':source,'target':target,'owner':owner,'stance':stance,'upgrade':upgrade,'shooter':shooter,'volume':volume,'x':x,'z':z})
        if mode=='SpeedCurve':
            k=0
            for rep in range(1,6):
                for speed_tag,speed in [('base',348),('upgraded',487.2),('fast',535.92)]:
                    for shooter in ('control','flat','cap','applied'):
                        x=-90000+(k%10)*18000;z=(k//10)*23000;k+=1
                        c=f'curve_{speed_tag}_{shooter}_r{rep}'
                        source=add(c+'_s','vgr_assaultfrigate' if shooter=='applied' else 'hwa_assault_'+shooter,[x+1000,0,z],1)
                        target=add(c+'_t','hwa_speed_'+speed_tag,[x,0,z-9000],0,1)
                        volume=c+'_end';volumes.append([volume,[x,0,z+17000],100])
                        cases.append({'id':c,'kind':'pass','source':source,'target':target,'owner':0,'stance':1,'upgrade':0,'shooter':shooter,'nominal_speed':speed,'volume':volume,'x':x,'z':z})
        if mode=='Progression':
            for owner in range(6):
                race='hgn' if owner%2==0 else 'vgr';c='progress_'+race+'_p'+str(owner)
                x=-60000+owner*22000;z=0
                first=add(c+'_first',race+'_mothership',[x,0,z],owner)
                second=add(c+'_second',race+'_carrier',[x,0,z+4000],owner)
                initial={0:['Research'],1:['Research'],2:['AdvancedResearch'],3:['FighterProduction'],4:['FighterProduction'],5:['Research','FighterProduction']}[owner]
                cases.append({'id':c,'kind':'progression','player':owner,'race':race,'first':first,'second':second,'initial_modules':initial,'initial_can_expected':1 if owner==5 else 0,'lab_count':1 if owner in (0,1) else 2,'speed_tech':'InterceptorMAXSPEEDUpgrade1' if race=='hgn' else 'FighterspeedUpgrade1','second_tech':'AttackBomberMAXSPEEDUpgrade1' if race=='hgn' else 'CorvetteTech','speed_cost':800 if race=='hgn' else 1200,'second_cost':400 if race=='hgn' else 500,'speed_time':30 if race=='hgn' else 45,'second_time':30 if race=='hgn' else 40,'x':x,'z':z})
        if mode in ('SaveLoad','SaveLoadAuto','SaveLoadTrace'):
            for j,race in enumerate(('kus','tai')):
                x=-40000+j*18000;z=-10000;c='save_'+race
                generator=('hwa_trace_' if mode=='SaveLoadTrace' else '')+race+'_gravwellgenerator'
                a=add(c+'_a',generator,[x-500,0,z],4+j)
                b=add(c+'_b',generator,[x+500,0,z],4+j)
                target=add(c+'_target',race+'_interceptor',[x,0,z+1200],4+j)
                enemy=add(c+'_enemy','hgn_interceptor',[x,0,z+1700],0,0)
                vgr=add(c+'_vgr','vgr_interceptor',[x+400,0,z+1700],1,0)
                cases.append({'id':c,'kind':'gravity','a':a,'b':b,'target':target,'enemy':enemy,'vgr':vgr,'x':x,'z':z})
        if mode=='GravityScope':
            for j,race in enumerate(('kus','tai')):
                x=-30000+j*60000;z=-10000;c='scope_'+race
                a=add(c+'_a',race+'_gravwellgenerator',[x-500,0,z],4+j)
                b=add(c+'_b',race+'_gravwellgenerator',[x+500,0,z],4+j)
                for k,(target_race,owner) in enumerate((('kus',4),('tai',5),('hgn',0),('vgr',1))):
                    name=c+'_'+target_race
                    target=add(name+'_target',target_race+'_interceptor',[x-600+k*400,0,z+1200],owner)
                    cases.append({'id':name,'kind':'gravity_scope','a':a,'b':b,'target':target,'driver':1 if k==0 else 0,'generator_race':race,'target_race':target_race,'x':x,'z':z})
        if mode in ('Economy6','Economy7'):
            for rep in range(3):
                z=-80000+rep*80000
                for owner,race,x,count in [(2*rep,'hgn',-80000,6),(2*rep+1,'vgr',80000,int(mode[-1]))]:
                    group='economy_'+race+'_r'+str(rep+1)
                    receiver='HWA_MotherH' if owner==0 else 'HWA_MotherV' if owner==1 else group+'_receiver'
                    if owner>=2:add(receiver,race+'_mothership',[x,0,z],owner)
                    for i in range(count):add(group+'_'+str(i),race+'_resourcecollector',[x-1000+i*300,0,z+2000],owner)
                    for i in range(48):asteroids.append(['Asteroid_3',[x+(i%8-4)*500,(i%3-1)*350,z+5000+(i//8)*600]])
                    cases.append({'id':group,'kind':'economy','player':owner,'race':race,'rep':rep+1,'count':count,'receiver':receiver,'members':[group+'_'+str(i) for i in range(count)]})
        if mode.startswith('EconomyMatrix'):
            configurations=[('mothership',5000,False),('carrier',13000,True),('resourcecontroller',7000,False)]
            for rep,(receiver_type,distance,mirror) in enumerate(configurations):
                z=-80000+rep*80000
                for offset,race,count in ((0,'hgn',6),(1,'vgr',int(mode[-1]))):
                    owner=rep*2+offset
                    x=(-100000 if offset==0 else 100000)*(-1 if mirror else 1)
                    group=f'matrix_{race}_r{rep+1}'
                    receiver='HWA_MotherH' if owner==0 else 'HWA_MotherV' if owner==1 else group+'_receiver'
                    add(receiver,race+'_'+receiver_type,[x,0,z],owner)
                    members=[add(group+'_'+str(i),race+'_resourcecollector',[x-1000+i*300,0,z+2000],owner) for i in range(count)]
                    for i in range(48):asteroids.append(['Asteroid_3',[x+(i%8-4)*500,(i%3-1)*350,z+distance+(i//8)*600]])
                    cases.append({'id':group,'kind':'economy_clean','player':owner,'race':race,'rep':rep+1,'count':count,'receiver':receiver,'receiver_type':receiver_type,'distance':distance,'mirrored':int(mirror),'members':members,'finish':600,'warmup':180,'steady_start':300,'x':x,'z':z})
        plans[mode]=cases;fixtures[mode]=ships
        path=f'leveldata/campaign/{CAMPAIGN}/{mode}'
        lines=['function DetermChunk()']
        for name,kind,pos,owner,size in ships:
            lines.extend([f'addSquadron({lua(name)},{lua(kind)},{lua(pos)},{owner},{{0,0,0}},{size},0)',f'createSOBGroup({lua(name)})',f'addToSOBGroup({lua(name)},{lua(name)})'])
        for name,pos,radius in volumes:lines.append(f'addSphere({lua(name)},{lua(pos)},{radius})')
        for kind,pos in asteroids:lines.append(f'addAsteroid({lua(kind)},{lua(pos)},100,0,0,0,0)')
        for c in cases:
            if 'x' in c:lines.append(f'addCamera({lua(c["id"])},{lua([c["x"],0,c["z"]+1000])},{lua([c["x"]+5000,6000,c["z"]-6000])})')
        races=('Hiigaran','Vaygr')*3 if mode.startswith('Economy') or mode in ('Progression','PaidProduction') else ('Hiigaran','Vaygr','Hiigaran','Vaygr','Kushan','Taiidan')
        lines.extend(['addCamera("HWA_Home",{-80000,0,-78000},{-72000,9000,-88000})','setWorldBoundsInner({0,0,0},{250000,100000,250000})','end','function NonDetermChunk()','loadBackground("m01")','setSensorsManagerCameraDistances(100,1000000)','end','maxPlayers='+str(len(races)),'levelDesc="$9985000"','player={}'])
        for p,race in enumerate(races):lines.append(f'player[{p}]={{id={p},name="",resources=0,raceName="{race}",startPos=0}}')
        put(path+'/'+mode+'.level','\n'.join(lines))
        put(path+'/'+mode+'.lua',f'HWA_MODE={lua(mode)}\nHWA_CASES={lua(cases)}\ndofilepath("data:scripts/hwmp24/autotests/runtime.lua")')
    put('scripts/hwmp24/autotests/salvage_cases.lua','HWS_CASES='+lua(plans['Salvage']+plans['SalvageBaselines']))
    put('scripts/hwmp24/autotests/dock_cases.lua','HWJ_CASES='+lua(plans['DockStall']))
    put('scripts/hwmp24/autotests/defense_cases.lua','HWD_CASES='+lua(plans['Defense']+plans['DefenseIdentity']+plans['DefenseOrders']+plans['DefenseIntercept']))
    strings={9985000:['HWMP 2.4 — автоматические испытания','HWMP 2.4 — Automatic Tests'],9985001:['Автоматический прогон. Не выдавайте приказы кораблям; результаты записываются в журнал.','Automatic run. Do not issue ship orders; results are recorded in the log.']}
    for i,mode in enumerate(MODES):strings[9985010+i]=[{'Mechanics':'Механика: гравиполя, ракеты и наука','Antistrike':'Противоистребительная стрельба: сравнение вариантов','Economy6':'Экономика: шесть сборщиков каждой расы','Economy7':'Экономика: шесть хиигарских и семь вэйгрских сборщиков','SaveLoad':'Гравиполя: сохранение и загрузка','SpeedCurve':'Скоростная кривая: изолированная проверка','Progression':'Наука: условия доступа и общая очередь','EconomyMatrix6':'Экономика 6/6: десять минут, три приёмника/маршрута','EconomyMatrix7':'Экономика 6/7: десять минут, три приёмника/маршрута','GravityScope':'Гравиполя: цели всех четырёх рас','SaveLoadAuto':'Гравиполя: автоматическая загрузка','SaveLoadTrace':'Гравиполя: загрузка с диагностикой callbacks','Defense':'Защитный истребитель: ракеты и охрана','DefenseIdentity':'Защитный истребитель: новые ракеты при том же счётчике','DefenseOrders':'Защитный истребитель: приказ атаки по ракетам','DefenseIntercept':'Защитный истребитель: реальная охрана корабля','SalvageBaselines':'Захват: сохранение исходного запрета самоуничтожения','GravityToggle':'Гравиполя: выключение и три пересекающихся источника','GravityExpiry':'Гравиполя: естественное завершение без сохранений','EconomyRecovery':'Добыча: настоящее повреждение модуля и восстановление приказа','Mines':'Мины: принудительная атака и штатный тральщик','CombatGeometry':'Бой: дистанция, высота, преследование и разворот','PaidProduction':'Стройка: настоящая платная очередь и старые/новые авианосцы','HW1Damage':'Наука HW1: оплаченные ступени урона истребителей','EconomyRaids':'Экономика: три отключения приёмников и запасной контроллер','ResearchEffects':'Наука: HP и скорость старых и новых кораблей','DockStall':'Стыковка: остановка под огнём и повтор приказа','Salvage':'Захват: доставка и прерывания буксировки','Transport':'Перевозка: стыковка, гиперпереход и освобождение'}[mode],mode+' automatic test']
    reg=(CACHE/'players-patch-audit/rm-base/locale/localedat.lua').read_text(encoding='ascii');put('locale/localedat.lua',reg[:reg.rfind('}')]+'{name="hwmp_autotests.dat"},\n}')
    for col,lang in enumerate(('Russian','English')):
        p=SOURCE/f'locale/{lang}/hwmp_autotests.ucs';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(''.join(str(n)+'\t'+v[col]+'\n' for n,v in sorted(strings.items())),encoding='utf-16',newline='\r\n')
    campaign=['displayName="$9985000"','contentName="'+CAMPAIGN+'"','contentType=2','contentOrdered=0','contentChooseText="$3492"','contentThumbName="$9985000"','contentThumbDesc="$9985001"','contentRules="SinglePlayer"','ExtFilter="campaign_gbx"','Mission={}']
    thumb=CACHE/'players-patch-audit/rm-campaign-hw2/ui/mapthumbnails/campaign/ascension/m03_staging.dds'
    shutil.copy2(thumb,SOURCE/f'leveldata/campaign/{CAMPAIGN}.dds')
    for i,mode in enumerate(MODES,1):
        campaign.append(f'Mission[{i}]={{postload=function() end,directory="{mode}",level="{mode}.level",postlevel=function() end,displayName="${9985009+i}",description="$9985001"}}')
        dst=SOURCE/f'ui/mapthumbnails/campaign/{CAMPAIGN}/{mode}.dds';dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(thumb,dst)
    put(f'leveldata/campaign/{CAMPAIGN}.campaign','\n'.join(campaign))
    inventory={n:sha(p) for n,p in index(SOURCE).items()};assert all(inventory[n]==h or n in diagnostic_overrides for n,h in base_hashes.items())
    run=hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest();put('scripts/hwmp24/autotests/run.lua','HWA_RUN="'+run+'"')
    save(WORK/'source.json',{'identity':IDENTITY,'run':run,'source':str(SOURCE),'base_files':base_hashes,'plans':plans,'fixtures':fixtures,'private_diagnostic_types':alterations,'diagnostic_overrides':diagnostic_overrides,'engine_tested':False})
    return run

def package():
    run=prepare();compiler=CACHE/'hwmp-testgrounds-step/lua4/lua-4.0.1/luac4-x86.exe'
    own=[p for n,p in index(SOURCE).items() if n not in json.loads((WORK/'source.json').read_text(encoding='utf8'))['base_files'] and p.suffix in ('.lua','.level','.campaign','.wepn','.wf','.ship')]
    own.append(SOURCE/'ui/newui/uisettings.lua')
    for p in own:
        r=subprocess.run([str(compiler),'-p',str(p)],capture_output=True,text=True);assert r.returncode==0,(p,r.stderr)
    from verify_save_compat import verify as verify_saver
    saver_report=verify_saver()
    verified=package_source(SOURCE,RELEASE,'HWMPAutoTests.big','HWMP Automatic Tests')
    for p in RELEASE.glob('*.log'):shutil.move(str(p),str(WORK/p.name))
    save(WORK/'verification.json',{'run':run,'lua4_files':len(own),'serializer':saver_report,'archives':verified['archives'],'full_extract_hash_comparison':True})
    save(RELEASE/'version.json',{'identity':IDENTITY,'run':run})
    save(WORK/'release.json',{'run':run,'files':{p.name:sha(p) for p in RELEASE.iterdir() if p.is_file()}})
    return {'run':run,'source':str(SOURCE),'release':str(RELEASE),'lua4_files':len(own)}

def install():
    mods=(GAME/'HomeworldRM/DataWorkshopMODs').resolve();target=(mods/'HWMPAutoTests').resolve();assert target.parent==mods and target.name=='HWMPAutoTests'
    assert not active_processes(GAME),'A game/launcher is running; do not replace its files'
    r=json.loads((WORK/'release.json').read_text(encoding='utf8'));assert all(sha(RELEASE/n)==h for n,h in r['files'].items())
    if target.exists():
        assert (target/'owner.txt').read_text().strip()==IDENTITY
        backup=WORK/'installed-backups'/(__import__('datetime').datetime.now().strftime('%Y%m%dT%H%M%S'))
        shutil.copytree(target,backup)
    before=other_mod_files(mods,target);target.mkdir(exist_ok=True)
    for n,h in r['files'].items():shutil.copy2(RELEASE/n,target/n);assert sha(target/n)==h
    (target/'owner.txt').write_text(IDENTITY+'\n');assert other_mod_files(mods,target)==before
    save(WORK/'installation.json',{'run':r['run'],'target':str(target),'files':r['files'],'other_mods_unchanged':True})
    return {'installed':str(target),'run':r['run']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--install',action='store_true');a=p.parse_args();print(json.dumps(install() if a.install else package()))
