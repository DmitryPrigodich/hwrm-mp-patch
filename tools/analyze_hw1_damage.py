"""Derived native invariants for the HW1 constant-hit diagnostic; not match balance."""
from collections import Counter

def summarize(plans,results,events):
    phases={}
    for e in events:
        if e['event']=='damage_phase_result':phases[e['case'],int(e['phase'])]=e
    checks=[]
    for row in results:
        c=plans[row['case']]
        start=1 if c['variant']=='new' else 0
        comparisons=[]
        for phase in range(start,3):
            measured=phases.get((c['id'],phase))
            reference=phases.get(('damage_'+c['race']+'_control'+str(c['rep']+1),phase))
            expected=1 if c['variant']=='control' else (0.75,0.875,1)[phase]
            ratio=None
            enough=False
            if measured and reference:
                enough=min(int(measured['positive_samples']),int(reference['positive_samples']))>=8
                if float(reference['min_positive_delta'])>0:
                    ratio=float(measured['min_positive_delta'])/float(reference['min_positive_delta'])
            passed=enough and ratio is not None and abs(ratio-expected)<0.001
            comparisons.append(dict(phase=phase,ratio=ratio,expected=expected,quorum=enough,passed=passed))
        passed=row['status']=='measured' and int(row['paid_spent'])==2200 and all(x['passed'] for x in comparisons)
        checks.append(dict(case=c['id'],status='passed' if passed else 'unresolved',phases=comparisons))
    return dict(counts=dict(Counter(x['status'] for x in checks)),checks=checks,
        limitations='Private constant-hit weapons; native paid research and BuildFamily, not whole-roster combat balance.')
