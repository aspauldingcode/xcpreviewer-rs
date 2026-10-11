"""Independent failure/settlement reader; pipe closure is not release evidence."""
import hashlib
import json
from pathlib import Path
import sys


def verify(folder):
    folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
    assert set(manifest['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}
    for name,row in manifest['files'].items():
        p=folder/name;assert '..' not in Path(name).parts and not p.is_symlink()
        b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
    rows=json.loads((folder/'controls/result.json').read_text())['controls']
    assert [r['mode'] for r in rows]==['observer-loss-held-stdio','output-pressure']
    for row in rows:
        assert row['error'] and row['observed']['pid']==row['observed']['group']
        record=row['record'];assert len(record['stdout'].encode())+len(record['stderr'].encode())<=1024
        assert record['signal']=='SIGKILL'
    loss,pressure=rows
    assert loss['record']['report']['drained'] is False
    assert loss['record']['emergencyClosed'] is True and 5000<=loss['elapsedMs']<6500
    assert loss['lateWritePresent'] is True
    assert (folder/'controls/observer-loss-held-stdio/late').read_bytes()==b'late'
    assert 'AssertionError' in loss['record']['report']['failure']
    assert pressure['record']['report']['drained'] is True
    assert pressure['record']['report']['remaining_observed']==0
    assert pressure['record']['report']['failure']=='abort'
    assert pressure['record']['emergencyClosed'] is False and pressure['elapsedMs']<2000
    assert pressure['lateWritePresent'] is False
    assert not (folder/'controls/output-pressure/late').exists()
    assert 'output limit' in pressure['error']
    return {'controls':2,'unknown_cleanup_rejected':True,'bounded_pipe_settlement':True,
            'mechanical_verification':'passed','scientific_delivery_review':'pending'}


if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),sort_keys=True))
