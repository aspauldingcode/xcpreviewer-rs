"""Independent bounded diagnostic expectations and frozen filesystem replay."""
import hashlib,json,subprocess,shutil,tempfile
from pathlib import Path
from reloop.primarysource import parse,expected

def verify(folder):
    folder=Path(folder);sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((folder/'manifest.json').read_text())
    assert set(m['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}
    for name,row in m['files'].items():
        p=folder/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts and not p.is_symlink();b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
    assert sha((folder/'fixture/manifest.json').read_bytes())=='c53084d90de41c1e42cb8c17a38cf3b70e4fa0e6551a5937a4de7d536272e4ac'
    d=json.loads((folder/'control/result.json').read_text());events=d['events'];diag=d['diagnostics'];assert len(events)==64 and diag['retainedEvents']==64 and diag['droppedEvents']==100
    assert diag['latest']==events[-1]=={'kind':'unavailable-source'} and diag['lastFailure']==events[-1]
    assert events[-2]=={'kind':'invalid-source'} and d['rejected']==80 and d['retainedBytes']==16384
    for i in range(0,62,2):
        observed,rejected=events[i:i+2];assert observed['kind']=='observed' and rejected['kind']=='rejected' and observed['generation']==rejected['generation']==51+i//2
        error=rejected['error'];assert type(error) is str and len(error.encode('utf-8'))<=512 and not any(ord(c)<32 or ord(c)==127 for c in error)
        original='Error: '+('🔥  '*4000);prefix=''
        for char in original:
            if len((prefix+char).encode('utf-8'))>512:break
            prefix+=char
        assert error==prefix
    source=(folder/'fixture/0-source.swift').read_bytes();oracle=expected(parse(source.decode()),64);assert (folder/'control/retained.raw').read_bytes()==oracle==(folder/'fixture/0-expected.raw').read_bytes()
    assert 'loop.diagnostics is not a function' in (folder/'before/control.stderr').read_text()
    # Independent expectations above, then fresh frozen production/control replay.
    with tempfile.TemporaryDirectory() as out:
        r=subprocess.run([shutil.which('node'),str(folder/'runtime/tools/re/tests/file_diagnostics_control.js'),str(folder/'fixture'),out],capture_output=True,timeout=15);assert r.returncode==0,r.stderr.decode()
        actual=json.loads((Path(out)/'result.json').read_text());assert actual==d and (Path(out)/'retained.raw').read_bytes()==oracle
    return {'rejections':80,'retained_events':64,'dropped_events':100,'complete_bytes':16384,'review':'pending'}
