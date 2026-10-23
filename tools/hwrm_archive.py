"""Campaign-independent native BIG packaging and complete payload verification."""
import struct
import subprocess
import shutil
from pathlib import Path
from hwrm_common import PROJECT,TOOL,short_path,index,sha,build_directory
ROOT=PROJECT
def runtime_file(path,root):return True

def native_aliases(path):
    with path.open('rb') as f:
        header=f.read(180)
        if header[:12]!=b'_ARCHIVE\x02\0\0\0':raise RuntimeError('Unexpected BIG format.')
        metadata_size=struct.unpack_from('<I',header,172)[0]
        if not 24<=metadata_size<16*1024*1024:raise RuntimeError('Invalid BIG metadata size.')
        metadata=f.read(metadata_size)
    offset,count=struct.unpack_from('<IH',metadata)
    if offset+138*count>len(metadata):raise RuntimeError('Invalid BIG TOC table.')
    aliases=[metadata[offset+i*138:offset+i*138+64].split(b'\0')[0].decode('ascii') for i in range(count)]
    if any(alias not in ('data','locale') for alias in aliases):
        raise RuntimeError('Unsupported native TOC alias: '+repr(aliases)+'. Package languages as sibling BIG files.')
    return aliases

def archive(manifest, output):
    for label,cmd in [('build',[str(TOOL),'-c',str(manifest),'-r',short_path(ROOT)+'\\','-a',str(output)]),('test',[str(TOOL),'-a',str(output),'-t'])]:
        proc=subprocess.run(cmd,capture_output=True,text=True)
        log=proc.stdout+proc.stderr
        output.with_suffix('.'+label+'.log').write_text(log,encoding='utf8')
        if proc.returncode or any(word in log for word in ('Error','ERROR','Failed','Could not')):
            raise RuntimeError(label+': '+log)
        if label=='test' and 'TEST: PASSED' not in log:
            raise RuntimeError('Archive test did not confirm success: '+log)
    native_aliases(output)

def localized_files(language):
    return sorted(p for p in (ROOT/f'locale/{language}').rglob('*') if p.is_file() and runtime_file(p,ROOT) and not (p.parent.name.lower()=='animatics' and p.name.lower().startswith('vre_')))

def locale_toc(language, name, short):
    # The native alias is "locale". Languages are selected by loading sibling
    # English.big / Russian.big, as documented by the shipped WorkshopTool.
    return [f'TOCStart name="{name}" alias="locale" relativeroot="locale\\{language}"',
            'FileSettingsStart defcompression="2"','FileSettingsEnd',
            *[short+'\\'+str(p.relative_to(ROOT)) for p in localized_files(language)],'TOCEnd']

def package_source(source,release,filename,title):
    global ROOT
    ROOT=Path(source).resolve();release=Path(release).resolve();release.mkdir(parents=True,exist_ok=True)
    short=short_path(ROOT)
    data=[short+'\\'+str(p.relative_to(ROOT)) for n,p in sorted(index(ROOT).items()) if not n.startswith('locale/')]
    manifest=release/'main.archive.txt'
    lines=['Archive name="'+title+'"','TOCStart name="ModData" alias="data" relativeroot=""','FileSettingsStart defcompression="2"','FileSettingsEnd',*data,'TOCEnd',*locale_toc('English','ModLocale',short),'']
    manifest.write_text('\r\n'.join(lines),encoding='ascii',newline='')
    output=release/filename;archive(manifest,output)
    for language in ('English','Russian'):
        manifest=release/(language+'.archive.txt')
        manifest.write_text('\r\n'.join(['Archive name="'+title+' '+language+'"',*locale_toc(language,'Mod'+language,short),'']),encoding='ascii',newline='')
        archive(manifest,release/(language+'.big'))
    verification=verify_payload(ROOT,output)
    for p in release.glob('*.archive.txt'):p.unlink()
    return verification

def verify_payload(source,output):
    results=[];sources=index(source)
    for path,language in [(Path(output),None),(Path(output).parent/'English.big','English'),(Path(output).parent/'Russian.big','Russian')]:
        work=build_directory('archive-verification',path.parent)
        target=work/('extracted-'+(language or 'main'))
        assert target.resolve().is_relative_to(work.resolve())
        if target.exists():shutil.rmtree(target)
        target.mkdir()
        proc=subprocess.run([str(TOOL),'-a',str(path),'-e',short_path(target)],capture_output=True,text=True)
        assert proc.returncode==0,('Archive extraction failed',path,proc.returncode)
        expected={}
        for name,source_path in sources.items():
            if not name.startswith('locale/'):
                if language is None:expected[name]=sha(source_path)
            elif name.startswith('locale/'+(language or 'English').lower()+'/'):
                expected[name.split('/',2)[2]]=sha(source_path)
        actual={name:sha(p) for name,p in index(target).items()}
        assert actual==expected,('Payload mismatch',path,sorted(set(actual)^set(expected)),[n for n in set(actual)&set(expected) if actual[n]!=expected[n]][:5])
        results.append({'archive':str(path),'sha256':sha(path),'files':len(expected),'aliases':native_aliases(path)})
    return {'status':'passed','archives':results,'full_extract_hash_comparison':True,'engine_tested':False,'installed':False}
