"""Summarize completed native HWMP tests; never promote observations to passes."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
from statistics import mean
from hwrm_common import PROJECT, save


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def latest_valid(runs):
    chosen = {}
    rejected = []
    for directory in sorted(runs.iterdir()):
        if not all((directory / n).is_file() for n in ('results.json','source.json','events.json','launch.json')):
            continue
        result, source, launch = [read(directory/n) for n in ('results.json','source.json','launch.json')]
        native=(directory/'native.txt').read_text(encoding='utf8') if (directory/'native.txt').is_file() else ''
        mode = result['mode']
        expected = {c['id'] for c in source['plans'][mode]}
        actual = [c['case'] for c in result['results']]
        valid = (result['status']=='finished' and not result['errors'] and not re.search(r'parameter:.*expected',native) and
                 result['run']==source['run']==launch['run'] and
                 len(actual)==len(set(actual)) and set(actual)==expected)
        if not valid:
            rejected.append({'directory':str(directory),'mode':mode,'reason':'incomplete, errors, or provenance/case mismatch'})
            continue
        chosen[mode]=(directory,result,source,read(directory/'events.json'))
    return chosen,rejected


def summarize(runs):
    chosen,rejected=latest_valid(runs)
    report={'native':True,'observations_are_not_balance_verdicts':True,'rejected_runs':rejected,'suites':{}}
    for mode,(directory,result,source,events) in chosen.items():
        plans={c['id']:c for c in source['plans'][mode]}
        suite={'directory':str(directory),'run':result['run'],'base_effects_sha256':source['base_files']['scripts/hwmp24/effects.lua'],'counts':dict(Counter(c['status'] for c in result['results'])),'cases':len(result['results'])}
        report['suites'][mode]=suite
        if mode.startswith('Defense'):
            from analyze_defense import summarize as defense_summary
            suite['defense']=defense_summary(plans,result['results'],events)
        if mode=='CombatGeometry':
            from analyze_geometry import summarize as geometry_summary
            suite['geometry']=geometry_summary(plans,result['results'],events)
        if mode=='HW1Damage':
            from analyze_hw1_damage import summarize as damage_summary
            suite['damage_upgrades']=damage_summary(plans,result['results'],events)
        if mode=='DockStall':
            from analyze_dock import summarize as dock_summary
            suite['dock']=dock_summary(plans,result['results'],events)
        groups=defaultdict(list)
        for row in result['results']:
            c=plans[row['case']]
            if mode=='SpeedCurve':
                tag=row['case'].split('_')[1]
                groups[(tag,c['shooter'],c['nominal_speed'])].append(row)
            elif mode=='CombatGeometry':groups[(c['shooter'],c['geometry'])].append(row)
            elif mode=='Antistrike':groups[(c['shooter'],c['upgrade'],c['stance'])].append(row)
            elif mode=='Mechanics' and c['kind']=='missile':groups[(c['launcher'],c['action'],c['armour'])].append(row)
        if mode in ('SpeedCurve','Antistrike','CombatGeometry'):
            suite['comparisons']=[]
            constants=next((e for e in events if e['event']=='native_constants'),{})
            stance_names={int(constants[k]):label for k,label in (('neutral','Neutral'),('evasive','Evasive'),('aggressive','Aggressive')) if k in constants}
            for key,rows in groups.items():
                case_ids={r['case'] for r in rows}
                native_stances=sorted({int(e['native_stance']) for e in events if e['case'] in case_ids and e['event']=='baseline' and 'native_stance' in e})
                suite['comparisons'].append({'group':key,'n':len(rows),'damage':[float(r['damage']) for r in rows],
                    'native_stances':native_stances,'target_stance_labels':[stance_names.get(s,'unknown') for s in native_stances],
                    'mean_damage':mean(float(r['damage']) for r in rows),
                    'mean_in_range_seconds':mean(float(r['in_range_seconds']) for r in rows),
                    'mean_peak_speed':mean(float(r['peak_speed']) for r in rows)})
        if mode=='Mechanics':
            suite['missiles']=[{'group':key,'n':len(rows),
                'primary_damage':[float(r['primary_damage']) for r in rows],
                'replacement_damage':[float(r['replacement_damage']) for r in rows],
                'statuses':[r['status'] for r in rows]} for key,rows in groups.items()]
            suite['mechanical_results']=[r for r in result['results'] if plans[r['case']]['kind']!='missile']
        if mode.startswith('EconomyMatrix'):
            suite['income']=[]
            for row in result['results']:
                c=plans[row['case']]
                ce=[e for e in events if e['case']==row['case']]
                baseline=int(next(e for e in ce if e['event']=='baseline')['ru'])
                first=next((e for e in ce if e['event']=='sample' and int(e['ru'])>baseline),None)
                late=[e for e in ce if e['event']=='sample' and float(e['t'])>=c['warmup']]
                mx=mean(float(e['t']) for e in late);my=mean(int(e['ru']) for e in late)
                denominator=sum((float(e['t'])-mx)**2 for e in late)
                rate=sum((float(e['t'])-mx)*(int(e['ru'])-my) for e in late)/denominator if denominator else None
                suite['income'].append({'case':row['case'],'race':c['race'],'rep':c['rep'],'collectors':c['count'],
                    'receiver_type':c['receiver_type'],'distance':c['distance'],'mirrored':c['mirrored'],
                    'first_credit_time':float(first['t']) if first else None,'income':int(row['income']),
                    'post_warmup_trend_ru_per_second':rate,
                    'after_warmup_income':int(row['after_warmup_income']),'last_300_income':int(row['last_300_income']),
                    'status':row['status']})
            suite['pairs']=[]
            for rep in sorted(set(r['rep'] for r in suite['income'])):
                pair={r['race']:r for r in suite['income'] if r['rep']==rep}
                h,v=pair['hgn'],pair['vgr']
                suite['pairs'].append({'rep':rep,'receiver_type':h['receiver_type'],'distance':h['distance'],
                    'hgn':h,'vgr':v,'vgr_to_hgn_total':v['income']/h['income'] if h['income'] else None,
                    'vgr_to_hgn_last_300':v['last_300_income']/h['last_300_income'] if h['last_300_income'] else None})
                suite['pairs'][-1]['vgr_to_hgn_post_warmup_trend']=v['post_warmup_trend_ru_per_second']/h['post_warmup_trend_ru_per_second'] if h['post_warmup_trend_ru_per_second'] else None
        elif mode in ('Economy6','Economy7'):
            suite['income']=[]
            for row in result['results']:
                case=row['case'];ce=[e for e in events if e['case']==case]
                samples=[e for e in ce if e['event']=='sample']
                disabled=next(e for e in ce if e['event']=='receiver_disabled_requested')
                cutoff=float(disabled['t'])
                before=[e for e in samples if float(e['t'])<cutoff]
                after=[e for e in samples if float(e['t'])>=cutoff]
                baseline=int(next(e for e in ce if e['event']=='baseline')['ru'])
                first=next((e for e in samples if int(e['ru'])>baseline),None)
                first_regen=next((e for e in after if float(e['receiver_hp'])>0.001),None)
                first_five=next((e for e in after if float(e['receiver_hp'])>=0.05),None)
                zero_hp=[e for e in after if float(e['receiver_hp'])<0.001]
                # Credit may continue from an in-progress unload. Report first observed
                # increment; do not identify it with reactivation of the receiver.
                previous=int(before[-1]['ru']);increments=[]
                for e in after:
                    if int(e['ru'])>previous:increments.append({'time':float(e['t']),'ru':int(e['ru']),'receiver_hp':float(e['receiver_hp'])})
                    previous=int(e['ru'])
                suite['income'].append({'case':case,'race':plans[case]['race'],'rep':plans[case]['rep'],
                    'collectors':plans[case]['count'],'first_credit_time':float(first['t']) if first else None,
                    'income_before_damage':int(before[-1]['ru'])-baseline,'final_income':int(row['income']),
                    'disabled_at':cutoff,'first_regeneration':first_regen,'first_five_percent':first_five,
                    'zero_hp_samples':len(zero_hp),'first_credit_after_damage':increments[0] if increments else None,
                    'credit_increments_after_damage':increments})
        if mode in ('SaveLoad','SaveLoadAuto','SaveLoadTrace','SaveLoadCold','SaveLoadEmpty','SaveLoadCoop','JournalPressure','JournalRecycle','Progression','GravityScope','Transport','Salvage','DockStall','SalvageBaselines','ResearchEffects','GravityToggle','GravityExpiry','HW1Damage','EconomyRaids','PaidProduction','EconomyRecovery','Mines','CombatGeometry'):suite['results']=result['results']
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',type=Path,default=PROJECT/'local/auto-tests/runs')
    p.add_argument('--out',type=Path,default=PROJECT/'local/auto-tests/summary.json')
    a=p.parse_args();report=summarize(a.runs);save(a.out,report)
    print(json.dumps({'report':str(a.out),'suites':{m:{k:v for k,v in s.items() if k in ('cases','counts','run')} for m,s in report['suites'].items()},'rejected_runs':len(report['rejected_runs'])},indent=2))
