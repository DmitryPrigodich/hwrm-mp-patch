"""Check actual source motion in the diagnostic; damage remains a measurement."""
from collections import Counter

def summarize(plans,results,events):
    checks=[]
    for row in results:
        c=plans[row['case']]
        samples=[e for e in events if e['case']==c['id'] and e['event']=='sample']
        speeds=[float(e['source_speed']) for e in samples]
        peak=max(speeds) if speeds else None
        moving=c.get('source_moving',0)==1
        motion_valid=peak is not None and (peak>10 if moving else peak<0.01)
        passed=row['status']=='measured' and motion_valid
        checks.append(dict(case=c['id'],moving_source_requested=moving,source_peak_speed=peak,
            status='passed' if passed else 'unresolved'))
    return dict(fixture_invariant_counts=dict(Counter(x['status'] for x in checks)),checks=checks,
        damage_is_not_a_balance_verdict=True)
