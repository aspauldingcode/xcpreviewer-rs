"""Independent pinned inputs, full allocation and Rust error receipt reader."""
import hashlib,json
from pathlib import Path
from reloop.livecorpus import CLI_RUN,CLI_ANCHOR,NATIVE_RUN,NATIVE_ANCHOR
from reloop.primarysource import expected

def verify(folder):
    folder=Path(folder);m=json.loads((folder/'manifest.json').read_text())
    assert set(m['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}
    for name,row in m['files'].items():
        p=folder/name;assert '..' not in Path(name).parts and not p.is_symlink()
        data=p.read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
    index=json.loads((folder/'control/inputs/corpus.json').read_text());assert index['pins']=={CLI_RUN:CLI_ANCHOR,NATIVE_RUN:NATIVE_ANCHOR}
    result=json.loads((folder/'control/result.json').read_text());rows=result['rows'];records=index['records'];assert len(rows)==len(records)==84
    native=0
    for n,(row,fixture) in enumerate(zip(rows,records)):
        c=fixture['config'];stride=fixture['stride'];assert row['index']==n and row['args']==[c['width'],c['height'],stride,131072,114688,16384,stride*c['height']]
        assert row['code']==0 and row['stdout']=='accepted 16384\n'
        actual=(folder/'control'/row['actual']).read_bytes();prediction=(folder/'control'/row['expected']).read_bytes()
        assert len(actual)==len(prediction)==16384 and actual==prediction==expected(c,stride)
        assert hashlib.sha256(prediction).hexdigest()+'.raw'==fixture['expected']
        assert row['native_bytes']==(16384 if fixture['native'] else 0);native+=row['native_bytes']
    controls=result['controls'];assert len(controls)==10
    for row in controls:
        assert row['code']==2
    for row,offset in zip(controls[:3],[0,52,16383]):
        assert row['offset']==offset and row['error']=='rejected Mismatch(%d)\n'%offset
        a=(folder/'control'/row['actual']).read_bytes();b=(folder/'control'/row['expected']).read_bytes()
        assert len(a)==len(b)==16384 and [i for i,(x,y) in enumerate(zip(a,b)) if x!=y]==[offset]
    assert [r['error'] for r in controls[3:]]==['rejected '+e+'\n' for e in ['Span','Span','Rendered','Capacity','Memory','Dimensions','Stride']]
    assert '5 passed; 0 failed' in (folder/'control/tests.stdout').read_text()
    assert native==1310720
    return {'frames':84,'compared_bytes':1376256,'native_reference_bytes':native,'negative_controls':10,'rust_tests':5,'scientific_delivery_review':'pending'}
