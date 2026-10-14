import hashlib
import json
import os
from pathlib import Path


def verify(folder):
    evidence = Path(folder)
    manifest = json.loads((evidence/'manifest.json').read_text())
    files = {str(path.relative_to(evidence)) for path in evidence.rglob('*') if path.is_file() and path.name != 'manifest.json'}
    assert set(manifest['files']) == files
    for name, expected in manifest['files'].items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        path = evidence/name
        assert not path.is_symlink()
        payload = path.read_bytes()
        assert len(payload) == expected['bytes'] and hashlib.sha256(payload).hexdigest() == expected['sha256']
    assert 'signal.signal(signal.SIGTERM,signal.SIG_IGN)' in (evidence/'target.py').read_text()
    assert json.loads((evidence/'slots.json').read_text()) == {'used':2,'limit':2}
    prediction = json.loads((evidence/'prediction.json').read_text())
    assert prediction['modes'] == ['running-0','running-1'] and prediction['child_raw_status'] == 9 and prediction['root_code'] == 43 and prediction['child_reaped_qualified'] is False
    identities = []
    for mode in prediction['modes']:
        root = evidence/mode
        assert json.loads((evidence/('wait-'+mode+'.json')).read_text()) == {'code':0,'timeout':False,'stdout':'owned stopped child exit pass\n','stderr':''}
        result = json.loads((root/'result.json').read_text())
        ready = json.loads((root/'ready.json').read_text())
        assert result['released'] is True and result['error'] == 'Error: Observed compiler failed: 43'
        record = result['record']
        assert record['privateAbortRequested'] is False and record['emergencyClosed'] is False
        report = record['report']
        assert report['drained'] is True and report['failure'] is None and report['target_code'] == 43 and report['tracked'] == 2 and report['remaining_observed'] == 0
        assert report == json.loads((root/'underlying-complete.json').read_text())
        registered = json.loads((root/'registered.json').read_text())
        assert registered['birth_rechecked'] is True and registered['stopped_requested'] is False and registered['child_status'] != 4
        assert registered['root_pid'] == ready['parent_pid'] and registered['child_pid'] == ready['child_pid']
        events = json.loads((root/'kernel-exit-events.json').read_text())
        assert len(events) == 2
        for event, pid, raw in zip(events,[ready['parent_pid'],ready['child_pid']],[43<<8,9]):
            assert event['pid'] == pid and event['data'] == raw and event['filter'] == -5 and event['flags'] == 32821 and event['fflags'] == 2214592512
        assert os.WIFSIGNALED(events[1]['data']) and os.WTERMSIG(events[1]['data']) == 9 and events[1]['exited'] is False
        watcher = json.loads((root/'watcher-wait.json').read_text())
        assert watcher['status'] == 0 and watcher['signal'] is None and watcher['error'] is None
        assert not (root/'child-wait.json').exists() and not (root/'child.raw').exists()
        identities.extend([ready['parent_pid'],ready['child_pid']])
    assert len(set(identities)) == 4
    return {'native_controls':2,'child_signals':[9,9],'root_codes':[43,43],'child_reaped_qualified':False}
