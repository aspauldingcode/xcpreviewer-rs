"""Independent byte reconstruction of owned supervisor writes and receipt results."""
import ast,hashlib,json
from pathlib import Path

def payload(path):
    tree=ast.parse(path.read_text());loop=next(n for n in tree.body if isinstance(n,ast.For))
    parts=ast.literal_eval(loop.iter);assert all(isinstance(p,list) and all(type(v) is int and 0<=v<=255 for v in p) for p in parts)
    return parts,b''.join(bytes(p) for p in parts)

def verify(folder):
    folder=Path(folder);m=json.loads((folder/'manifest.json').read_text())
    assert set(m['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}
    for name,row in m['files'].items():
        p=folder/name;assert '..' not in Path(name).parts and not p.is_symlink()
        data=p.read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
    before=json.loads((folder/'before/result.json').read_text())['controls'];after=json.loads((folder/'after/result.json').read_text())['controls']
    modes=['split-utf8','invalid-utf8','ascii-bytewise']
    assert [r['mode'] for r in before]==[r['mode'] for r in after]==modes
    assert all(r['error'] is None for r in before)
    assert before[0]['record']['report']['scope']=='owned-\ufffd\ufffd'
    assert before[1]['record']['report']['scope']=='owned-\ufffd\ufffd'
    assert after[0]['error'] is None and after[0]['record']['report']['scope']=='owned-é'
    assert 'not valid for encoding utf-8' in after[1]['error'] and after[1]['record']['report'] is None
    assert after[2]['error'] is None and after[2]['record']['report']['scope']=='owned-ascii'
    compared=0
    for mode in modes:
        parts,data=payload(folder/'before'/mode/'owned-supervisor');other,afterbytes=payload(folder/'after'/mode/'owned-supervisor')
        assert parts==other and data==afterbytes;compared+=len(data)
        if mode=='split-utf8':
            assert parts[0][-1]==195 and parts[1][0]==169
            assert json.loads(data.decode('utf8'))['scope']=='owned-é'
        elif mode=='invalid-utf8':
            assert 255 in data
            try:data.decode('utf8')
            except UnicodeDecodeError:pass
            else:raise AssertionError('Invalid control became valid')
        else:
            assert all(len(p)==1 for p in parts) and json.loads(data.decode('ascii'))['scope']=='owned-ascii'
    for row in after:
        assert row['elapsedMs']<3000 and row['record']['signal']=='SIGKILL'
        assert row['record']['emergencyClosed'] is False
    return {'controls':3,'paired_payload_bytes':compared,'utf8_preserved':True,'invalid_rejected':True,'scientific_delivery_review':'pending'}
