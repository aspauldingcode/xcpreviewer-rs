"""Independent sealed-receipt verification for the owned POSIX source gate."""
import hashlib
import json
from pathlib import Path
import sys


def verify(folder):
    folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
    actual={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}
    assert actual==set(manifest['files'])
    for name,row in manifest['files'].items():
        p=folder/name;assert not p.is_symlink() and '..' not in Path(name).parts
        data=p.read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
    before=json.loads((folder/'before-result.json').read_text())
    assert before['timed_out'] is True and before['stdout']=='entered\n'
    result=json.loads((folder/'after/result.json').read_text())
    kinds=['fifo','directory','symlink','missing','regular','fifo-race','symlink-race']
    assert [r['kind'] for r in result['controls']]==kinds
    for r in result['controls']:
        assert r['builds']==(1 if r['kind']=='regular' else 0)
        assert r['opened']==r['closed']==(1 if r['kind'] in ('regular','fifo-race') else 0)
        assert r['raced'] is r['kind'].endswith('-race')
        assert r['elapsedMs']<1200
        s=r['status'];assert s['loopClosed'] is True and s['building'] is False
        assert s['timers']==s['liveWorkers']==0
    assert result['controls'][0]['deadlineAutoClosed'] is True
    return {'controls':7,'mechanical_verification':'passed','scientific_delivery_review':'pending'}


if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),sort_keys=True))
