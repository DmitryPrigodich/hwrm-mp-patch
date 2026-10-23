"""Extract local native inputs with the official Archive tool; never run a game."""
import json
import subprocess
from pathlib import Path
from hwrm_common import PROJECT,CACHE,DONOR,RUSSIAN_STOCK,ARCHIVE,DONOR_SHA,GAME,TOOL,index,sha,save,short_path

def extract(archive,target):
    target=Path(target).resolve()
    assert target.is_relative_to(CACHE.resolve())
    if target.exists() and any(target.iterdir()):return
    target.mkdir(parents=True,exist_ok=True)
    result=subprocess.run([str(TOOL),'-a',str(archive),'-e',short_path(target)],capture_output=True,text=True)
    assert result.returncode==0,('Extraction failed',archive,result.returncode)

def prepare():
    assert ARCHIVE.is_file() and sha(ARCHIVE)==DONOR_SHA,'Supply the pinned Test21 archive through local/settings.json.'
    extract(ARCHIVE,DONOR)
    expected={row['path']:row['sha256'] for row in json.loads((PROJECT/'baseline/test-inventory.json').read_text())['inventory']}
    assert {n:sha(p) for n,p in index(DONOR).items()}==expected,'The extracted donor differs.'
    extract(GAME/'HomeworldRM/Data/Russian.big',RUSSIAN_STOCK)
    assert any(RUSSIAN_STOCK.glob('*.ucs')),'Stock Russian UCS files are missing.'
    report={'status':'passed','donor_sha256':DONOR_SHA,'files':len(expected),'asset_cache':str(CACHE),'game_launched':False}
    save(PROJECT/'local/inputs.json',report);print(json.dumps(report))

if __name__=='__main__':prepare()
