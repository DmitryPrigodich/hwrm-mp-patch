"""Native flight/attack geometry; resilient targets retain stock geometry/armour."""
import re

def prepare(put,clone_ship,native):
    for race in ('hgn','vgr'):
        def transform(s):
            s=re.sub(r'^NewShipType.maxhealth=.*$', 'NewShipType.maxhealth=100000',s,flags=re.M)
            s=re.sub(r'^NewShipType.(?:regentime|minRegenTime)=.*$',lambda m:m[0].split('=')[0]+'=0',s,flags=re.M)
            s=re.sub(r'^NewShipType.(?:mainEngineMaxSpeed|thrusterMaxSpeed)=(.+)$',lambda m:m[0].split('=')[0]+'=('+m[1]+')*1.4',s,flags=re.M)
            return s
        clone_ship(race+'_interceptor','hwa_geometry_'+race,transform)

def cases(add,volumes):
    result=[]
    for shooter,source,source_owner,race,owner in [('assault','vgr_assaultfrigate',1,'hgn',2),('flak','hgn_assaultfrigate',0,'vgr',3)]:
        for geometry in ('near_cross','edge_cross','high_cross','pursuit','pursuit_up','turn'):
            for rep in range(3):
                k=len(result);x=-100000+k%6*40000;z=-90000+k//6*35000
                name='geometry_'+shooter+'_'+geometry+str(rep)
                start=[x-3000,0,z+800];end=[x+7000,0,z+800]
                if geometry=='edge_cross':start=[x-3500,0,z+2400];end=[x+7500,0,z+2400]
                elif geometry=='high_cross':start=[x-3500,1800,z+800];end=[x+7500,1800,z+800]
                elif geometry=='pursuit':start=[x,0,z+1800];end=[x,0,z+30000]
                elif geometry=='pursuit_up':start=[x,0,z+1800];end=[x,20000,z+25000]
                s=add(name+'_source',source,[x,0,z],source_owner)
                target=add(name+'_target','hwa_geometry_'+race,start,owner,0)
                volume=name+'_end';volumes.append([volume,end,100])
                turn=name+'_turn';volumes.append([turn,[x-7000,2000,z+800],100])
                result.append(dict(id=name,kind='pass',shooter=shooter,source=s,source_player=source_owner,target=target,
                    owner=owner,stance=2,upgrade='private_maxspeed_x1.4',geometry=geometry,rep=rep,
                    source_moving=1 if geometry.startswith('pursuit') else 0,turn_volume=turn,
                    volume=volume,x=x,z=z))
    return result
