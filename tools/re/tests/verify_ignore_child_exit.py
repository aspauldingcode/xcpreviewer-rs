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
    assert (evidence/'observed_compiler.js').read_bytes() == (Path(__file__).resolve().parents[1]/'reloop/observed_compiler.js').read_bytes()
    watcher_identity = json.loads((evidence/'watcher.json').read_text())
    rea = json.loads((evidence/'rea-status.json').read_text())
    assert rea['server']['name'] == 'rea' and rea['server']['version'] == '6.2.0'
    assert rea['watcher']['architecture'] == 'arm64' and rea['watcher']['sha256'] == watcher_identity['sha256'] == '464058e04ba8cb220cbfb6ebb5d550f63deb48dc0d8031a67d54e7076dc3176d'
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
        assert result['mode'] == mode and result['code'] == 43 and result['policy'] == 'running'
        assert ready['child_ack'] == 'ready'
        proxy = json.loads((root/'anchor-pid.json').read_text())
        rows = [row for batch in result['observed'] for row in batch]
        parent = next(row for row in rows if row['pid'] == ready['parent_pid'])
        child = next(row for row in rows if row['pid'] == ready['child_pid'])
        runtime = '/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python'
        launcher = '/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'
        assert parent['parent'] == proxy['anchor_pid'] and parent['group'] == ready['parent_group'] == proxy['proxy_group']
        assert child['parent'] == parent['pid'] and child['group'] == child['pid']
        for row in [parent,child]:
            identity = row['identity']
            assert len(identity) == 3 and type(identity[0]) is int and identity[0] > 0 and type(identity[1]) is int and 0 <= identity[1] < 1000000
            assert identity[2] in [runtime,launcher]
        assert child['identity'][2] == runtime
        assert json.loads((root/'release-observation.json').read_text()) == next(batch for batch in result['observed'] if child in batch)
        record = result['record']
        assert record['privateAbortRequested'] is False and record['emergencyClosed'] is False
        assert record['pid'] == proxy['proxy_group'] and record['anchorCode'] is None and record['signal'] == 'SIGKILL'
        for stream in ['stdout','stderr']:
            assert record[stream] == '' and record[stream+'Bytes'] == 0 and record[stream+'Sha256'] == hashlib.sha256(b'').hexdigest()
        report = record['report']
        assert report['drained'] is True and report['failure'] is None and report['target_code'] == 43 and report['tracked'] == 2 and report['remaining_observed'] == 0
        assert report == json.loads((root/'underlying-complete.json').read_text())
        assert report['kind'] == 'complete' and type(report['observations']) is int and report['observations'] > 0
        assert report['scope'] == 'Observed full-identity ancestry and inherited group only; unseen escapes excluded'
        registered = json.loads((root/'registered.json').read_text())
        assert registered['birth_rechecked'] is True and registered['stopped_requested'] is False and type(registered['child_status']) is int and registered['child_status'] in [1,2,3,5,6]
        assert registered['note_exit'] == 2147483648 and registered['note_exitstatus'] == 67108864
        assert registered['root_pid'] == ready['parent_pid'] and registered['child_pid'] == ready['child_pid']
        events = json.loads((root/'kernel-exit-events.json').read_text())
        assert len(events) == 2
        for event, pid, raw in zip(events,[ready['parent_pid'],ready['child_pid']],[43<<8,9]):
            assert event['pid'] == pid and event['data'] == raw and event['filter'] == -5 and event['flags'] == 32821 and event['fflags'] == 2214592512
        assert os.WIFSIGNALED(events[1]['data']) and os.WTERMSIG(events[1]['data']) == 9 and events[1]['exited'] is False
        assert events[0]['exited'] is True and events[0]['exit_code'] == 43 and events[1]['exit_code'] == -1
        watcher = json.loads((root/'watcher-wait.json').read_text())
        assert watcher['status'] == 0 and watcher['signal'] is None and watcher['error'] is None
        assert watcher['stdout'] == watcher['stderr'] == ''
        assert (root/'gate').read_bytes() == b'go' and not (root/'stopped-marker.raw').exists() and not (root/'retained-failure.json').exists()
        assert not (root/'child-wait.json').exists() and not (root/'child.raw').exists()
        identities.extend([ready['parent_pid'],ready['child_pid']])
    assert len(set(identities)) == 4
    return {'native_controls':2,'child_signals':[9,9],'root_codes':[43,43],'child_reaped_qualified':False}
