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
        groups=defaultdict(list)
        for row in result['results']:
            c=plans[row['case']]
            if mode=='SpeedCurve':
                tag=row['case'].split('_')[1]
                groups[(tag,c['shooter'],c['nominal_speed'])].append(row)
            elif mode=='Antistrike':groups[(c['shooter'],c['upgrade'],c['stance'])].append(row)
            elif mode=='Mechanics' and c['kind']=='missile':groups[(c['launcher'],c['action'],c['armour'])].append(row)
        if mode in ('SpeedCurve','Antistrike'):
            suite['comparisons']=[]
            for key,rows in groups.items():
                suite['comparisons'].append({'group':key,'n':len(rows),'damage':[float(r['damage']) for r in rows],
                    'mean_damage':mean(float(r['damage']) for r in rows),
                    'mean_in_range_seconds':mean(float(r['in_range_seconds']) for r in rows),
                    'mean_peak_speed':mean(float(r['peak_speed']) for r in rows)})
        if mode=='Mechanics':
            suite['missiles']=[{'group':key,'n':len(rows),
                'primary_damage':[float(r['primary_damage']) for r in rows],
                'replacement_damage':[float(r['replacement_damage']) for r in rows],
                'statuses':[r['status'] for r in rows]} for key,rows in groups.items()]
            suite['mechanical_results']=[r for r in result['results'] if plans[r['case']]['kind']!='missile']
        if mode.startswith('Economy'):
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
        if mode in ('SaveLoad','Progression'):suite['results']=result['results']
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',type=Path,default=PROJECT/'local/auto-tests/runs')
    p.add_argument('--out',type=Path,default=PROJECT/'local/auto-tests/summary.json')
    a=p.parse_args();report=summarize(a.runs);save(a.out,report)
    print(json.dumps({'report':str(a.out),'suites':{m:{k:v for k,v in s.items() if k in ('cases','counts','run')} for m,s in report['suites'].items()},'rejected_runs':len(report['rejected_runs'])},indent=2))
