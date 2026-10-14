import hashlib
import json
from pathlib import Path


def verify(folder):
    evidence = Path(folder)
    manifest = json.loads((evidence/'manifest.json').read_text())
    assert set(manifest['files']) == {str(path.relative_to(evidence)) for path in evidence.rglob('*') if path.is_file() and path.name != 'manifest.json'}
    for name, expected in manifest['files'].items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        payload = (evidence/name).read_bytes()
        assert not (evidence/name).is_symlink() and len(payload) == expected['bytes'] and hashlib.sha256(payload).hexdigest() == expected['sha256']
    assert hashlib.sha256((evidence/'anchor.py').read_bytes()).hexdigest() == 'c10b94507a190fc464ea9d5d33abc1f2199c3543ddc9be31573c97f85d2b14cd'
    assert json.loads((evidence/'slots.json').read_text()) == {'used':2,'limit':2}
    expected = bytes([0,1,2,255,10,42,99,128])
    outcomes = []
    for mode in ['baseline','delayed']:
        root = evidence/mode
        result = json.loads((root/'result.json').read_text())
        record = result['record']
        assert result['mode'] == mode and result['error'] == ('Error: Observed compiler failed: deadline' if mode == 'delayed' else None)
        report = record['report']
        assert report['drained'] is True and report['target_code'] == 0 and report['remaining_observed'] == 0 and report['failure'] == ('deadline' if mode == 'delayed' else None)
        assert record['emergencyClosed'] is False and record['privateAbortRequested'] is False and record['signal'] == 'SIGKILL'
        assert (root/'owned.raw').read_bytes() == expected
        assert record['stdoutBytes'] == 8 and record['stdoutSha256'] == hashlib.sha256(expected).hexdigest() and record['stdout'] == expected.decode('utf8',errors='replace')
        assert record['stderrBytes'] == 0 and record['stderr'] == '' and record['stderrSha256'] == hashlib.sha256(b'').hexdigest()
        assert json.loads((evidence/('wait-'+mode+'.json')).read_text()) == {'code':0,'stdout':'owned post-completion delay pass\n','stderr':'','timeout':False}
        rows = [json.loads(line) for line in (root/'deadline-audit.jsonl').read_text().splitlines()]
        assert 0 < len(rows) < 512 and [row['sequence'] for row in rows] == list(range(1,len(rows)+1))
        assert rows[0]['milliseconds'] == 1000 and rows[0]['anchor_sha256'] == 'c10b94507a190fc464ea9d5d33abc1f2199c3543ddc9be31573c97f85d2b14cd'
        base = next(row for row in rows if row['kind'] == 'anchor_clock' and row['line'] == 45)
        deadline = base['value']+1
        spawn = next(row for row in rows if row['kind'] == 'target_spawn')
        assert spawn['anchor_pid'] == record['pid'] and spawn['pid'] != record['pid']
        terminal = next(row for row in rows if row['kind'] == 'target_poll' and row['code'] is not None)
        assert terminal['pid'] == spawn['pid'] and terminal['code'] == 0 and terminal['value'] < deadline
        decisions = [row for row in rows if row['kind'] == 'anchor_clock' and row['line'] == 101]
        assert decisions and decisions[0]['sequence'] > terminal['sequence']
        starts = [row for row in rows if row['kind'] == 'injected_delay_start']
        ends = [row for row in rows if row['kind'] == 'injected_delay_end']
        if mode == 'delayed':
            assert len(starts) == len(ends) == 1
            start, end = starts[0], ends[0]
            assert start['deadline'] == deadline and start['terminal_observed_at'] < deadline and terminal['value'] <= start['value'] < deadline < end['value'] <= decisions[0]['value']
            assert terminal['sequence'] < start['sequence'] < end['sequence'] < decisions[0]['sequence']
        else:
            assert starts == ends == [] and all(row['value'] < deadline for row in decisions)
        outcomes.append({'mode':mode,'target_wait_code':0,'first_terminal_poll_minus_deadline':terminal['value']-deadline,'deadline_verdict':mode == 'delayed'})
    return {'owned_peer_jobs':2,'native_compiler_builds':0,'controlled_payload_bytes':16,'outcomes':outcomes,'post_completion_reclassification_observed':True,'historical_timing_qualified':False}
