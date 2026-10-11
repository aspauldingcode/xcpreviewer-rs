"""Fresh-context schema-control reader; no native identity authenticity claim."""
import json,hashlib
from pathlib import Path

def verify(folder):
    folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
    assert set(manifest['files']) == {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}
    for name,row in manifest['files'].items():
        p=folder/name;assert '..' not in Path(name).parts and not p.is_symlink()
        data=p.read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
    before=json.loads((folder/'before/result.json').read_text())['controls']
    after=json.loads((folder/'after/result.json').read_text())['controls']
    modes=['null-group','negative-parent','invalid-microseconds','missing-group']
    assert [r['mode'] for r in before]==[r['mode'] for r in after]==modes
    for row in before[:3]:
        assert row['error'] is None and row['record']['report']['drained'] is True
        assert row['record']['report']['target_code']==0
    assert before[-1]['error'] and before[-1]['record']['report']['drained'] is False
    for row in after:
        assert row['error'] and 'AssertionError' in row['record']['report']['failure']
        assert row['record']['report']['drained'] is False
        assert row['record']['report']['target_code'] is None
        assert row['record']['signal']=='SIGKILL' and row['record']['emergencyClosed'] is False
        assert row['elapsedMs']<2000
    return {'controls':4,'prior_false_acceptances':3,'malformed_rejected':True,'scientific_delivery_review':'pending'}
