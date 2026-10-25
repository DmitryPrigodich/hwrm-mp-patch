"""Launch/collect only this task's isolated native automatic test processes."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import zlib
from hwrm_common import PROJECT,GAME,sha,save
from auto_testgrounds import WORK,MODES
from install_hwmp24 import active_processes

LOG=GAME/'HomeworldRM/Bin/Release/HwRM.log'
CURRENT=WORK/'current-process.json'

def readlog():
    raw=LOG.read_bytes() if LOG.exists() else b''
    encoding='utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf8'
    return raw.decode(encoding,errors='replace').replace('\0','')

def status():
    run=json.loads(CURRENT.read_text(encoding='utf-8-sig'))
    text=readlog();events=[]
    for line in text.splitlines():
        i=line.find('HWMP_AUTO|')
        if i<0:continue
        fields=dict(x.split('=',1) for x in line[i+10:].split('|') if '=' in x)
        if fields.get('run')!=run['run'] or fields.get('mode')!=run['mode']:continue
        events.append(fields)
    results=[e for e in events if e.get('event')=='result']
    ended=any(e.get('event')=='end' and e.get('case')=='suite' for e in events)
    errors=sorted(set(x for x in text.splitlines() if re.search(r'attempt to|stack traceback|LUA.*(?:error|ERROR)|WEAPON FIRE ERROR|parameter:.*expected|FATAL|Assertion failed',x)))
    report={'pid':run['pid'],'mode':run['mode'],'run':run['run'],
            'status':'finished' if ended else 'fatal_error' if errors else 'waiting_for_load' if run['mode']=='SaveLoad' and any(e.get('event')=='save_requested' for e in events) and not any(e.get('event')=='save_loaded' for e in events) else 'running',
            'events':len(events),'game_time':float(events[-1]['t']) if events else None,
            'result_counts':dict(Counter(e.get('status') for e in results)),
            'results':results,'errors':errors}
    return run,report,events,text

def launch(mode):
    assert not active_processes(GAME),'Do not interrupt a running game/launcher'
    installed=json.loads((WORK/'installation.json').read_text(encoding='utf8'))
    release=json.loads((WORK/'release.json').read_text(encoding='utf8'))
    assert installed['run']==release['run']
    for n,h in installed['files'].items():assert sha(Path(installed['target'])/n)==h,n
    directory=WORK/'runs'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+mode)
    directory.mkdir(parents=True)
    if LOG.is_file():shutil.copy2(LOG,directory/'preceding-HwRM.log')
    exe=GAME/'HomeworldRM/Bin/Release/HomeworldRM.exe'
    command=[str(exe),'-workshopmod',r'HWMPAutoTests\HWMPAutoTests.big',
             '-campaign','HWMPAutoTests','-startinglevel',mode,'-windowed','-w','1600','-h','900','-locale','Russian','-luatrace','-nomovies']
    process=subprocess.Popen(command,cwd=exe.parent,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    data={'pid':process.pid,'mode':mode,'run':installed['run'],'directory':str(directory),
          'started_at_utc':datetime.now(timezone.utc).isoformat(),'command':command,'archives':installed['files']}
    save(CURRENT,data);save(directory/'launch.json',data)
    shutil.copy2(WORK/'source.json',directory/'source.json')
    return {'launched':True,'mode':mode,'pid':process.pid,'directory':str(directory)}

def collect(close=False):
    run,report,events,text=status()
    directory=Path(run['directory']).resolve();assert directory.is_relative_to((WORK/'runs').resolve())
    shutil.copy2(LOG,directory/'HwRM.log')
    save(directory/'results.json',report);save(directory/'events.json',events)
    (directory/'native.txt').write_text(text,encoding='utf8')
    report['log_sha256']=sha(directory/'HwRM.log')
    if run['mode']=='SaveLoad':
        label='HWMP_AutoFields_'+run['run'][:8]
        candidates=[]
        for path in (GAME/'HomeworldRM/Bin/Profiles').glob('*/Campaign/HWMPAUTOTESTS/*.sav'):
            if label.encode('utf-16le') in path.read_bytes():candidates.append(path)
        if len(candidates)==1:
            path=candidates[0];shutil.copy2(path,directory/'checkpoint.sav')
            checkpoint={'file':str(path),'label':label,'sha256':sha(path),'run':run['run'],
                        'real_load_confirmed':any(e.get('event')=='save_loaded' for e in events)}
            decoder=zlib.decompressobj(31)
            payload=decoder.decompress(path.read_bytes())
            checkpoint['unsafe_scout_hash_export']=b'SCOUT SPEED LIMITER =' in payload
            checkpoint['safe_scout_hash_export']=b'SCOUTSPEEDLIMITER =' in payload
            save(directory/'checkpoint.json',checkpoint)
            report['checkpoint_label']=label
        else:report['checkpoint_matches']=len(candidates)
    save(directory/'results.json',report)
    if close:
        assert report['status'] in ('finished','fatal_error'),'Never close an unfinished healthy suite'
        pid=int(run['pid'])
        script=f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}'; if ($p) {{ if ($p.Name -ne 'HomeworldRM.exe' -or $p.CommandLine -notlike '*HWMPAutoTests*') {{throw 'Refusing a non-test process'}}; Stop-Process -Id {pid} }}"
        result=subprocess.run(['powershell.exe','-NoProfile','-Command',script],capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        report['managed_process_closed']=True;save(directory/'results.json',report)
    return {k:v for k,v in report.items() if k not in ('results',)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--launch',choices=MODES);p.add_argument('--collect',action='store_true');p.add_argument('--close',action='store_true');a=p.parse_args()
    result=launch(a.launch) if a.launch else collect(a.close) if a.collect else {k:v for k,v in status()[1].items() if k!='results'}
    print(json.dumps(result,ensure_ascii=False,indent=2))
