"""200 configured target entries under six original generators; no physical hull claim."""
def cases(add,volumes):
    out=[]
    for row,race in enumerate(('kus','tai')):
        x=-40000+row*80000;z=0;name='pressure_'+race;owner=4+row
        sources=[add(name+'_g'+str(i),race+'_gravwellgenerator',[x-500+i*500,0,z],owner) for i in range(3)]
        members=[add(name+'_t'+str(i),('hgn' if i%2==0 else 'vgr')+'_scout',[x-600+(i%10)*120,0,z+800+i//10*100],i%2,1) for i in range(100)]
        volume=name+'_end';volumes.append([volume,[x+5000,0,z+1200],100])
        out.append(dict(id=name,kind='journal_pressure',members=members,sources=sources,volume=volume,x=x,z=z))
    return out
