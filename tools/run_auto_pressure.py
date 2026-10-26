"""One native pressure sample; wall time is not FPS or pure CPU time."""
from pathlib import Path
import sys,time,json
from run_auto_tests import launch,collect,readlog,CURRENT,LOG
from hwrm_common import save,sha
started=launch('JournalPressure');print(json.dumps(started),flush=True)
metadata=json.loads(CURRENT.read_text());times={};deadline=time.monotonic()+600
while time.monotonic()<deadline:
    if metadata.get('preceding_log_sha256') and LOG.exists() and sha(LOG)==metadata['preceding_log_sha256']:
        time.sleep(0.2);continue
    text=readlog();now=time.monotonic()
    for line in text.splitlines():
        if 'HWMP_AUTO|' not in line or 'run='+metadata['run'] not in line:continue
        fields=dict(x.split('=',1) for x in line.split('HWMP_AUTO|',1)[1].split('|') if '=' in x)
        if fields.get('mode')!='JournalPressure':continue
        for event in ('pressure_baseline','pressure_steady','result','end'):
            if fields.get('event')==event:
                key=fields.get('case','suite')+':'+event
                if key not in times:times[key]=dict(wall=now,game=float(fields['t']))
    if 'suite:end' in times:
        report=collect(close=True);save(Path(started['directory'])/'performance.json',times)
        print(json.dumps(report),flush=True);print(json.dumps(times),flush=True);break
    if any(token in text for token in ('stack traceback:','FATAL EXIT','WEAPON FIRE ERROR')):
        print(json.dumps(collect(close=True)),flush=True);raise SystemExit('Native error')
    time.sleep(0.2)
else:raise SystemExit('Healthy timeout left open')
