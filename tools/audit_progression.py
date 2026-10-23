"""Pinned Hgn/Vgr progression audit and explicit, unboosted reference schedules.

These schedules are data models, not measured opening times or optimal builds.
Uses the existing passive Classic reader and strict HWRM data-table loader.
"""
import argparse
import json
import re
from hwrm_common import PROJECT, ARCHIVE, DONOR_SHA, save, sha
from hwrm_inspect import record_config
from lua4_data import tables as classic_tables
from audit_economy import Sources, VERSIONS, data_table

PIN = PROJECT/'baseline/progression-inputs.json'
WORK = PROJECT/'local/progression-audit'
TARGETS = {
    'hiigaran': ('interceptor','attackbomber','assaultcorvette','pulsarcorvette',
        'minelayercorvette','torpedofrigate','assaultfrigate','ioncannonfrigate',
        'marinefrigate','defensefieldfrigate','destroyer','carrier','shipyard','battlecruiser'),
    'vaygr': ('interceptor','bomber','lancefighter','missilecorvette','lasercorvette',
        'commandcorvette','minelayercorvette','assaultfrigate','heavymissilefrigate',
        'infiltratorfrigate','destroyer','carrier','shipyard','battlecruiser'),
}


def definition(sources, version, relative):
    path, proof = sources.use(version,relative)
    if version=='classic':
        values, calls = classic_tables(path)
        cfg = next(values[k] for k in ('NewShipType','NewSubSystemType') if k in values)
        calls = [(c['name'],c['args'][1:]) for c in calls]
    else:
        text = path.read_text(encoding='utf-8-sig').replace('StartSubSystemConfig()','StartShipConfig()')
        cfg, calls = record_config(text)
    return {'source':proof,'values':cfg,'calls':calls}


def all_caps(sources, version, race):
    paths = ['scripts/unitcaps/normal.lua'] if version=='classic' else [
        'scripts/rules/deathmatch/unitcaps/normal.lua',
        f'scripts/races/{race}/deathmatch/unitcaps/normal.lua']
    result = {}
    for rel in paths:
        p,_ = sources.use(version,rel)
        if version=='classic':
            _, calls = classic_tables(p)
            for c in calls:
                n,a = c['name'],c['args']
                if n in ('UC_Family','UC_ShipType'): result[a[0]]=a[1]
                elif n in ('UC_FamilyOverride','UC_ShipTypeOverride') and a[0].lower()==race: result[a[1]]=a[2]
        else:
            result.update({k:float(v) for k,v in re.findall(
                r'^\s*supplyLimit\("([^"\n]+)"\s*,\s*([\d.]+)\)',p.read_text(),re.M)})
    return result


def needed(expr):
    # Choose the base Research branch and also require the production component.
    # This stronger condition satisfies both plausible &/| precedence orders.
    expr = (expr or '').strip().replace('Research | AdvancedResearch','Research')
    if not expr: return []
    if '|' in expr or not re.fullmatch(r'[\w\s&]+',expr):
        raise ValueError('Route requires an explicit alternative: '+expr)
    return [s.strip() for s in expr.split('&') if s.strip()]


def satisfied(expr, facts):
    """Accept only if both normal AND precedence and left-to-right give true."""
    if not expr or not expr.strip(): return True
    tokens = re.split(r'\s*([&|])\s*',expr.strip())
    assert len(tokens)%2==1 and all(t in ('&','|') for t in tokens[1::2]), expr
    vals = [t.strip().lower() in facts for t in tokens[::2]]
    left = vals[0]
    for op,val in zip(tokens[1::2],vals[1:]):
        left = (left and val) if op=='&' else (left or val)
    terms = [vals[0]]
    for op,val in zip(tokens[1::2],vals[1:]):
        if op=='&': terms[-1] = terms[-1] and val
        else: terms.append(val)
    return left and any(terms)


class Plan:
    def __init__(self, catalog, prefix, fast_bc=False):
        self.c = catalog; self.p = prefix; self.fast_bc = fast_bc
        self.actions = {}; self.tail = {}; self.busy = set(); self.slots = {}
        self.hosts = {'ms':prefix+'_mothership','c':prefix+'_carrier'}
        self.host_ready = {'ms':None,'c':None}
        self.cap_host = 'ms'

    def add(self, key, kind, item, host, deps):
        if key in self.actions: return key
        cfg = self.c['build'][item] if kind!='research' else self.c['research'][item]
        cost = cfg['Cost'] if kind=='research' else self.c['definitions'][item]['values'].get('buildCost',self.c['definitions'][item]['values'].get('costToBuild'))
        duration = cfg['Time'] if kind=='research' else self.c['definitions'][item]['values'].get('buildTime',self.c['definitions'][item]['values'].get('timeToBuild'))
        queue = None if kind=='research' and cost==0 and duration==0 else ('research' if kind=='research' else host+':'+kind)
        deps = list(dict.fromkeys(x for x in deps if x))
        if queue in self.tail and self.tail[queue] not in deps: deps.append(self.tail[queue])
        start = max([self.actions[x]['end'] for x in deps]+[0])
        self.actions[key] = {'id':key,'kind':kind,'item':item,'host':host,'queue':queue,
                             'cost':cost,'duration':duration,'start':start,'end':start+duration,'deps':deps}
        if queue: self.tail[queue]=key
        return key

    def module(self, type_string, host=None):
        if host is None:
            host = 'c' if type_string in ('Research','AdvancedResearch') else self.cap_host if type_string=='CapShipProduction' else 'ms'
        stem = {'Research':'module_research','AdvancedResearch':'module_researchadvanced',
                'FighterProduction':'production_fighter','CorvetteProduction':'production_corvette',
                'FrigateProduction':'production_frigate','CapShipProduction':'production_capship',
                'Hyperspace':'module_hyperspace','PlatformProduction':'module_platformcontrol'}[type_string]
        code = 'c' if host=='c' else 'sy' if host=='sy' and type_string=='CapShipProduction' else 'ms'
        item = f'{self.p}_{code}_{stem}'
        key = host+':'+item
        if key in self.actions: return key
        assert key not in self.busy, ('Dependency cycle',key)
        self.busy.add(key)
        row = self.c['build'][item]
        deps = [self.host_ready[host]]
        deps += [self.module(t) for t in needed(row.get('RequiredFleetSubSystems',''))]
        deps += [self.module(t,host) for t in needed(row.get('RequiredShipSubSystems',''))]
        deps += [self.tech(t) for t in needed(row.get('RequiredResearch',''))]
        self.can_build(host,item)
        hardpoints = [a for n,a in self.c['definitions'][self.hosts[host]]['calls'] if n=='StartShipHardPointConfig']
        candidates = [a[0] for a in hardpoints if item in [str(x).lower() for x in a[6:]]]
        slot = next((s for s in candidates if (host,s) not in self.slots),None)
        assert slot is not None, ('No free hardpoint',host,item,candidates)
        self.slots[(host,slot)] = item
        self.busy.remove(key)
        self.add(key,'subsystem',item,host,deps)
        self.actions[key]['type_string'] = self.c['definitions'][item]['values']['typeString']
        self.actions[key]['hardpoint'] = slot
        return key

    def tech(self, name):
        key = 'research:'+name
        if key in self.actions: return key
        assert key not in self.busy, ('Research cycle',name)
        self.busy.add(key)
        row = self.c['research'][name]
        assert not row.get('AIOnly') and name not in self.c['mp_research_restrict'], name
        assert not row.get('RequireTag'), ('Route needs tag validation',name)
        deps = [self.tech(t) for t in needed(row.get('RequiredResearch',''))]
        deps += [self.module(t) for t in needed(row.get('RequiredSubSystems',''))]
        self.busy.remove(key)
        return self.add(key,'research',name,None,deps)

    def can_build(self,host,item):
        families = next(a[2] for n,a in self.c['definitions'][self.hosts[host]]['calls']
                        if n=='addAbility' and a[0]=='CanBuildShips')
        assert self.c['definitions'][item]['values']['BuildFamily'] in [s.strip() for s in families.split(',')], (host,item)

    def ship(self,item,host='ms'):
        key = host+':'+item
        row = self.c['build'][item]
        deps = [self.host_ready[host]]
        deps += [self.module(t,host) for t in needed(row.get('RequiredShipSubSystems',''))]
        deps += [self.module(t) for t in needed(row.get('RequiredFleetSubSystems',''))]
        deps += [self.tech(t) for t in needed(row.get('RequiredResearch',''))]
        self.can_build(host,item)
        return self.add(key,'ship',item,host,deps)

    def run(self,target):
        if target.endswith('_battlecruiser'):
            if self.fast_bc: self.module('CapShipProduction','ms')
            yard = self.ship(self.p+'_shipyard')
            self.hosts['sy'] = self.p+'_shipyard'; self.host_ready['sy']=yard
            self.cap_host = 'ms' if self.fast_bc else 'sy'
            result = self.ship(target,'sy')
        else: result = self.ship(target)
        self.verify()
        return {'cost':sum(a['cost'] for a in self.actions.values()),'seconds':self.actions[result]['end'],
                'actions':list(self.actions.values()),'native_engine_tested':False}

    def roster(self,targets):
        results=[self.ship(t) for t in targets]
        self.verify()
        return {'cost':sum(a['cost'] for a in self.actions.values()),
                'seconds':max(self.actions[k]['end'] for k in results),
                'actions':list(self.actions.values()),'native_engine_tested':False}

    def verify(self):
        for a in self.actions.values():
            before = [b for b in self.actions.values() if b['id']!=a['id'] and b['end']<=a['start']]
            global_subs = {b['type_string'].lower() for b in before if b['kind']=='subsystem'}
            local_subs = {b['type_string'].lower() for b in before if b['kind']=='subsystem' and b['host']==a['host']}
            techs = {b['item'].lower() for b in before if b['kind']=='research'}
            if a['kind']=='research':
                r = self.c['research'][a['item']]
                assert satisfied(r.get('RequiredSubSystems',''),global_subs), a
            else:
                r = self.c['build'][a['item']]
                assert satisfied(r.get('RequiredShipSubSystems',''),local_subs), a
                assert satisfied(r.get('RequiredFleetSubSystems',''),global_subs), a
            assert satisfied(r.get('RequiredResearch',''),techs), a
            for dep in a['deps']: assert self.actions[dep]['end']<=a['start']
        for queue in self.tail:
            rows = sorted((a for a in self.actions.values() if a['queue']==queue),key=lambda a:a['start'])
            assert all(a['end']<=b['start'] for a,b in zip(rows,rows[1:])), queue


def catalog(sources, version, race):
    prefix = 'hgn' if race=='hiigaran' else 'vgr'
    folder = f'scripts/building and research/{race}' if version=='classic' else f'scripts/races/{race}/scripts'
    build,_ = data_table(sources,version,folder+('/build.lua' if version=='classic' else '/def_build.lua'),'build')
    research,_ = data_table(sources,version,folder+('/research.lua' if version=='classic' else '/def_research.lua'),'research',True)
    builds = {r['ThingToBuild'].lower():r for r in build.values()}
    assert len(builds)==len(build), ('Duplicate build target',version,race)
    assert len({r['Name'] for r in research.values()})==len(research), ('Duplicate research name',version,race)
    definitions = {}
    for ident,row in builds.items():
        kind,ext = ('ship','ship') if row['Type']==0 else ('subsystem','subs')
        definitions[ident] = definition(sources,version,f'{kind}/{ident}/{ident}.{ext}')
    for ident in (prefix+'_mothership',prefix+'_carrier',prefix+'_shipyard',prefix+'_ms_module_buildspeed'):
        if ident not in definitions:
            kind,ext = ('subsystem','subs') if '_module_' in ident else ('ship','ship')
            definitions[ident] = definition(sources,version,f'{kind}/{ident}/{ident}.{ext}')
    blocked = set()
    if version!='classic':
        rel=f'scripts/races/{race}/deathmatch/props/gbx.lua'
        props,_=data_table(sources,version,rel,'String_Properties')
        blocked.update(x.strip() for x in props.get('generic_mp_research_restrict','').split(',') if x.strip())
        sources.use(version,'scripts/scar/restrict.lua')
    return {'build':builds,'research':{r['Name']:r for r in research.values()},
            'definitions':definitions,'mp_research_restrict':sorted(blocked),'caps':all_caps(sources,version,race)}


def changes(before, after):
    fields = ('Cost','Time','RequiredResearch','RequiredSubSystems','UpgradeValue','UpgradeName','TargetType','TargetName','RequireTag','DoNotGrant','AIOnly')
    result = {}
    for name in sorted(set(before)|set(after)):
        a,b=before.get(name,{}),after.get(name,{})
        delta={k:[a.get(k),b.get(k)] for k in fields if a.get(k)!=b.get(k)}
        if delta: result[name]=delta
    return result


def audit(pin_inputs=False):
    assert sha(ARCHIVE)==DONOR_SHA
    sources = Sources(); data={}; routes={}
    for version in VERSIONS:
        data[version]={}; routes[version]={}
        for race in TARGETS:
            c=catalog(sources,version,race);data[version][race]=c;routes[version][race]={}
            prefix='hgn' if race=='hiigaran' else 'vgr'
            for name in TARGETS[race]:
                target=prefix+'_'+name
                routes[version][race][target]=Plan(c,prefix).run(target)
                if name=='battlecruiser':
                    routes[version][race][target+':extra_ms_capital_facility']=Plan(c,prefix,True).run(target)
            roster = ('assaultfrigate','ioncannonfrigate','marinefrigate') if race=='hiigaran' else ('heavymissilefrigate','assaultfrigate','infiltratorfrigate')
            routes[version][race]['three_frigate_roles']=Plan(c,prefix).roster([prefix+'_'+n for n in roster])
    inputs={'schema':1,'test21_archive_sha256':DONOR_SHA,'layers':VERSIONS,
            'files':dict(sorted(sources.used.items())),'resolution':dict(sorted(sources.resolution.items()))}
    inputs=json.loads(json.dumps(inputs))
    if pin_inputs:
        if PIN.exists(): raise RuntimeError('Input pin already exists; inspect before replacing.')
        save(PIN,inputs)
    assert PIN.exists() and json.loads(PIN.read_text(encoding='utf8'))==inputs, 'Progression inputs changed.'
    delta={race:changes(data['pp23'][race]['research'],data['test21'][race]['research']) for race in TARGETS}
    report={'native_engine_tested':False,'runtime_changed':False,'input_files':len(sources.used),
            'pin_sha256':sha(PIN),'catalog':data,'reference_routes':routes,'test_vs_pp23_research_changes':delta,
            'schedule_assumptions':['unlimited RU; no combat, loss, travel or launch delay',
                'starting MS and carrier with empty module slots; research on carrier, production on MS',
                'one research queue and one subsystem queue per hull; separate ship queue',
                'base durations, no production boosts; zero-cost/zero-time helper treated as immediate',
                'both plausible &/| precedences validated; stronger requirements used for route',
                'prescribed reference routes, not optimized or measured earliest builds']}
    for version in data.values():
        for race,c in version.items():
            p='hgn' if race=='hiigaran' else 'vgr'
            assert p+'_ms_module_buildspeed' not in c['build']
    assert routes['test21']['hiigaran']['hgn_destroyer']['seconds']==355
    assert routes['test21']['vaygr']['vgr_destroyer']['seconds']==390
    assert routes['test21']['hiigaran']['hgn_assaultfrigate']['cost']==5450
    assert routes['test21']['vaygr']['vgr_assaultfrigate']['cost']==4500
    assert routes['test21']['hiigaran']['three_frigate_roles']['cost']==6850
    assert routes['test21']['vaygr']['three_frigate_roles']['cost']==7000
    save(WORK/'audit.json',report)
    print(json.dumps({'report':str(WORK/'audit.json'),'input_files':len(sources.used),
                      'validated_reference_routes':sum(len(r) for v in routes.values() for r in v.values()),
                      'native_engine_tested':False,'runtime_changed':False}))
    return report


def write_tables(report):
    names={'classic':'Classic','remastered':'HWRM','pp23':'PP 2.3','test21':'Test21'}
    lines=['# Контрольные маршруты прогрессии Hgn/Vgr','',
           'Генерируется tools/audit_progression.py --write-tables из закреплённых данных. Не редактировать числа вручную.',
           '', 'Каждая ячейка — суммарные RU / базовые секунды указанного маршрута. Два стартовых производителя бесплатны, RU неограниченны; наука на авианосце, производство на Материнском Корабле, BC — на верфи. Это предписанные планы без боевых/ресурсных задержек и ускорений, не оптимальные и не измеренные открытия. Нулевой InstaAdvancedFrigateTech считается мгновенным. Смешанные &/| условия проверяются в двух трактовках с более строгими предпосылками.',
           '', 'Объяснение, реальные ограничения и кандидаты — [PROGRESSION_AUDIT.md](PROGRESSION_AUDIT.md).','']
    for race in TARGETS:
        lines += ['## '+('Хиигаряне' if race=='hiigaran' else 'Вэйгры'),'',
                  '| Проект / вариант | '+' | '.join(names.values())+' |',
                  '|---|'+'---|'*4]
        for target in report['reference_routes']['test21'][race]:
            values=[]
            for version in names:
                route=report['reference_routes'][version][race][target]
                values.append(f"{route['cost']:g} / {route['seconds']:g}")
            lines.append('| '+target+' | '+' | '.join(values)+' |')
        lines.append('')
    (PROJECT/'docs/PROGRESSION_ROUTES.md').write_text('\n'.join(lines).rstrip()+'\n',encoding='utf8',newline='\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pin-inputs',action='store_true')
    parser.add_argument('--write-tables',action='store_true')
    args=parser.parse_args();report=audit(args.pin_inputs)
    if args.write_tables:write_tables(report)
