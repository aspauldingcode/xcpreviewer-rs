"""Independent private-envelope and owned cancellation reader; not Canvas transport."""
import hashlib,json
from pathlib import Path

def verify(folder):
    folder=Path(folder);m=json.loads((folder/'manifest.json').read_text())
    assert set(m['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}
    for name,row in m['files'].items():
        p=folder/name;assert '..' not in Path(name).parts and not p.is_symlink()
        data=p.read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
    before=json.loads((folder/'before/result.json').read_text())['controls']
    after=json.loads((folder/'after/result.json').read_text())['controls']
    modes=['valid','trailing-partial','missing-accounting','negative-count','boolean-count']
    assert [r['mode'] for r in before]==[r['mode'] for r in after]==modes
    assert all(r['error'] is None for r in before)
    assert after[0]['error'] is None
    assert after[0]['record']['report']['tracked']==1 and after[0]['record']['report']['observations']==1
    assert 'truncated trailing data' in after[1]['error']
    # A well-formed leading receipt does not rescue a truncated envelope.
    assert after[1]['record']['report']['drained'] is True
    for row in after[2:]:
        assert row['error'] and row['record']['report'] is None
    for row in after:
        assert row['elapsedMs']<2000 and row['record']['signal']=='SIGKILL'
        assert row['record']['emergencyClosed'] is False
    boundary=json.loads((folder/'cancel-fixed/result.json').read_text())
    original=boundary['original'];new=boundary['reparented'];r=boundary['record'];report=r['report']
    assert original['pid']==new['pid']==original['group']==new['group']
    assert original['identity']==new['identity'] and original['parent']!=new['parent']
    assert 'aborted' in boundary['error'] and r['privateAbortRequested'] is True
    assert report['target_code']==0 and report['drained'] is True and report['remaining_observed']==0
    assert report['tracked']>=2 and r['emergencyClosed'] is False
    assert boundary['lateWriteAbsent'] is True and not (folder/'cancel-fixed/late').exists()
    first=json.loads((folder/'cancel-diagnosis/diagnostic.json').read_text())
    assert 'PermissionError' in first['error'] and first['record']['report']['drained'] is False
    return {'terminal_controls':5,'previous_false_acceptances':4,'reparent_abort_controls':1,
            'mechanical_verification':'passed','scientific_delivery_review':'pending'}
