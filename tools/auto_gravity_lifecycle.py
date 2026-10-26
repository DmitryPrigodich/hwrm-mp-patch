"""Native CustomCommand toggles/energy completion, no saved state or helper calls."""

def cases(add,volumes,mode):
    result=[]
    for j,race in enumerate(('kus','tai')):
        x=-50000+j*100000;z=10000;name=('toggle_' if mode=='GravityToggle' else 'expiry_')+race
        sources=[add(name+'_'+str(k),race+'_gravwellgenerator',[x-500+k%3*500,0,z+k//3*350],4+j) for k in range(9 if mode=='GravityToggle' else 1)]
        for k,(target_race,owner) in enumerate([('kus',4),('tai',5),('hgn',0),('vgr',1)]):
            ident=name+'_'+target_race;p=[x-900+k*600,0,z+1200]
            target=add(ident+'_target',target_race+'_interceptor',p,owner,0 if target_race in ('hgn','vgr') else 1)
            destination=ident+'_move';volumes.append([destination,[p[0],0,p[2]+1500],100])
            result.append(dict(id=ident,kind='gravity_lifecycle',mode=mode,sources=sources,target=target,owner=owner,
                driver=1 if k==0 else 0,destination=destination,x=x,z=z))
    return result
