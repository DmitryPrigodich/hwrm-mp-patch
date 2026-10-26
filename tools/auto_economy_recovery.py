"""Distinguish API damage artifact, real subsystem shots, and harvest-order recovery."""

def cases(add,volumes,asteroids):
    result=[]
    for row,method in enumerate(('api','real_shots','api_reissue')):
        z=-70000+row*70000
        for offset,race in enumerate(('hgn','vgr')):
            owner=row*2+offset;enemy=1-offset;x=-100000 if offset==0 else 100000;name='recovery_'+race+'_'+method
            receiver='HWA_MotherH' if owner==0 else 'HWA_MotherV' if owner==1 else name+'_mother'
            add(receiver,race+'_mothership',[x,0,z],owner)
            members=[add(name+'_'+str(j),race+'_resourcecollector',[x-1000+j*300,0,z+2000],owner) for j in range(6)]
            source='';spawn=name+'_attacker_spawn';volumes.append([spawn,[x,0,z-3500],50])
            if method=='real_shots':source=add(name+'_attacker','vgr_battlecruiser',[x,0,z-3500],enemy)
            for j in range(48):asteroids.append(['Asteroid_3',[x+(j%8-4)*500,(j%3-1)*350,z+5000+j//8*600]])
            result.append(dict(id=name,kind='economy_recovery',race=race,player=owner,enemy=enemy,method=method,
                receiver=receiver,members=members,source=source,source_player=enemy,spawn=spawn,x=x,z=z))
    return result
