"""Native SpaceMine targets held in place; no shipped weapon coefficients changed."""
from pathlib import Path
import re,shutil

def prepare(put,clone_ship,native,source):
    name='hwa_stationary_mine'
    text=native['missile/vgr_mine/vgr_mine.miss'].read_text(encoding='ascii')
    text=re.sub(r'^NewShipType.detectionDistance=.*$', 'NewShipType.detectionDistance=0',text,flags=re.M)
    text=re.sub(r'^NewShipType.(?:mainEngineMaxSpeed|thrusterMaxSpeed)=.*$',lambda m:m[0].split('=')[0]+'=1',text,flags=re.M)
    put(f'missile/{name}/{name}.miss',text)
    for ext in ('.hod','.events'):
        key='missile/vgr_mine/vgr_mine'+ext
        if key in native:
            target=source/f'missile/{name}/{name}{ext}';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(native[key],target)
        elif ext=='.hod':raise AssertionError(key)
    fire=native['scripts/weaponfire/vgr_mine/vgr_mine.wf'].read_text(encoding='ascii')
    fire,n=re.subn(r'scartype\s*=\s*"[^"]+"','scartype = "'+name+'/'+name+'"',fire)
    assert n==1
    put(f'scripts/weaponfire/{name}/{name}.wf',fire)
    weapon=native['weapon/vgr_minelayer/vgr_minelayer.wepn'].read_text(encoding='ascii').replace('"Vgr_Mine"','"'+name+'"')
    put('weapon/hwa_mine_launcher/hwa_mine_launcher.wepn',weapon)
    def transform(s):
        s=re.sub(r'^StartShipWeaponConfig\([^\n]*(?:Vgr_MinelayerCannon|Vgr_MineSweeperBurstCannon)[^\n]*\n?', '',s,flags=re.M)
        return s.replace('"Vgr_MineLayer"','"hwa_mine_launcher"')
    clone_ship('vgr_minelayercorvette','hwa_mine_deployer',transform)

def cases(add,volumes):
    result=[]
    for kind in ('vgr_assaultfrigate','hgn_gunturret','vgr_weaponplatform_gun','vgr_minelayercorvette'):
        for fire in (0,1):
            k=len(result);x=-100000+k%4*60000;z=-50000+k//4*100000;name='mines_'+str(k)
            shooter=add(name+'_source',kind,[x,0,z],0)
            deployer=add(name+'_deployer','hwa_mine_deployer',[x,0,z+1000],1)
            sensor=add(name+'_sensor','hgn_proximitysensor',[x+500,0,z+1000],0)
            volume=name+'_field';volumes.append([volume,[x,0,z+1000],100])
            result.append(dict(id=name,kind='mine_attack',shooter_kind=kind,fire=fire,source=shooter,source_player=0,
                deployer=deployer,sensor=sensor,volume=volume,selection=name+'_selection',snapshot=name+'_snapshot',alive=name+'_alive',x=x,z=z))
    return result
