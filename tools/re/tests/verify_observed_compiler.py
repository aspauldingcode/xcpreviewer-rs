"""Separate integrity/control/full-allocation reader; no delivery attestation."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]


def verify(folder):
    folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
    actual={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}
    # Nested compiler manifests are ordinary sealed artifacts too.
    actual.update(str(p.relative_to(folder)) for p in folder.rglob('manifest.json') if p!=folder/'manifest.json')
    assert actual==set(manifest['files'])
    for name,row in manifest['files'].items():
        p=folder/name;assert '..' not in Path(name).parts and not p.is_symlink()
        b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
    result=json.loads((folder/'controls/result.json').read_text())
    assert result['preabort'] is True
    assert [r['mode'] for r in result['controls']]==['success','failure','timeout','abort']
    for row in result['controls']:
        observed=row['observed'];assert observed['pid']==observed['group']
        assert len(observed['identity'])==3 and observed['identity'][2].startswith('/')
        report=row['record']['report'];assert report['drained'] is True
        assert report['remaining_observed']==0 and report['tracked']>=2 and report['observations']>0
        assert report['failure']=={'success':None,'failure':None,'timeout':'deadline','abort':'abort'}[row['mode']]
        assert report['target_code']=={'success':0,'failure':7,'timeout':-15,'abort':-15}[row['mode']]
        assert row['record']['signal']=='SIGKILL' and row['lateWriteAbsent'] is True
        assert not (folder/'controls'/row['mode']/'late').exists()
        assert (row['error'] is None)==(row['mode']=='success')
    source=ROOT/'research/evidence/source-revision-2026-10-10'
    assert hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest()=='c53084d90de41c1e42cb8c17a38cf3b70e4fa0e6551a5937a4de7d536272e4ac'
    references={r['path']:r for r in json.loads((source/'manifest.json').read_text())['files']}
    for i in range(3):
        frame=(folder/'fresh/result'/('%d-frame.raw'%i)).read_bytes()
        name='%d-expected.raw'%i;expected=(source/name).read_bytes()
        assert hashlib.sha256(expected).hexdigest()==references[name]['sha256']
        assert len(frame)==len(expected)==16384 and frame==expected
    builds=json.loads((folder/'fresh/result/compiler-result.json').read_text())['builds']
    assert len(builds)==3 and all(r['cacheHit'] is False for r in builds)
    return {'controls':4,'fresh_allocation_bytes':49152,'mechanical_verification':'passed','scientific_delivery_review':'pending'}


def verify_private(folder):
    folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
    assert set(manifest['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}
    for name,row in manifest['files'].items():
        p=folder/name;assert not p.is_symlink() and '..' not in Path(name).parts
        b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
    before=json.loads((folder/'before.json').read_text())['control']['record']
    assert before['report']['target_code']==1 and 'BlockingIOError' in before['stderr']
    after=json.loads((folder/'after.json').read_text())
    assert after['stdout']=='stdin-closed\n' and after['report']['target_code']==0
    assert after['report']['drained'] is True and after['report']['remaining_observed']==0
    return {'target_stdin_eof':True,'mechanical_verification':'passed'}


if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),sort_keys=True))
