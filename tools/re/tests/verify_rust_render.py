"""Independent Fraction/native anchors and full Rust-produced allocation reader."""
import hashlib,json
from pathlib import Path
from reloop.livecorpus import CLI_RUN,CLI_ANCHOR,NATIVE_RUN,NATIVE_ANCHOR
from reloop.primarysource import expected

def verify(folder):
    folder=Path(folder);m=json.loads((folder/'manifest.json').read_text())
    assert set(m['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}
    for name,row in m['files'].items():
        p=folder/name;assert '..' not in Path(name).parts and not p.is_symlink();data=p.read_bytes()
        assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
    result=json.loads((folder/'control/result.json').read_text());index=json.loads((folder/'control/inputs/corpus.json').read_text())
    assert index['pins']=={CLI_RUN:CLI_ANCHOR,NATIVE_RUN:NATIVE_ANCHOR}
    assert len(result['rows'])==len(index['records'])==84;native=0
    for n,(row,fixture) in enumerate(zip(result['rows'],index['records'])):
        c=fixture['config'];stride=fixture['stride'];assert row['index']==n and row['args']==[c['width'],c['height'],stride,*c['alphas'],c['reverse']]
        actual=(folder/'control'/row['actual']).read_bytes();oracle=expected(c,stride)
        assert len(actual)==16384 and actual==oracle==(folder/'control'/row['expected']).read_bytes()
        assert hashlib.sha256(actual).hexdigest()==row['sha256'] and row['code']==0
        assert row['stdout']=='rendered %d 16384\n'%(stride*c['height'])
        assert row['native_bytes']==(16384 if fixture['native'] else 0);native+=row['native_bytes']
        if fixture['native']:assert actual==(folder/'control/inputs'/fixture['native']).read_bytes()
    controls=result['controls'];assert [r['kind'] for r in controls]==['width','height','stride','alpha','order']
    for row,error in zip(controls,['Dimensions','Dimensions','Stride','Alpha','Unsupported primary order']):
        assert row['code']==2 and row['error']=='rejected '+error+'\n' and row['unchanged'] is True
        assert (folder/'control'/row['target']).read_bytes()==b'owned-output-sentinel'
    assert '7 passed; 0 failed' in (folder/'first-tests.stdout').read_text()
    assert native==1310720
    return {'rust_render_frames':84,'complete_bytes':1376256,'native_reference_bytes':native,'invalid_controls':5,'rust_tests':7,'scientific_delivery_review':'pending'}
