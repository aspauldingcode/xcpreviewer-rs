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
    outcomes = []
    for index, expected_code in [(0,-15),(1,0)]:
        case = evidence/('case-'+str(index))
        stage = next((case/'builds').glob('build-*'))
        rows = [json.loads(line) for line in (stage/'deadline-audit.jsonl').read_text().splitlines()]
        assert 0 < len(rows) < 512 and [row['sequence'] for row in rows] == list(range(1,len(rows)+1))
        identity = rows[0]
        assert identity['kind'] == 'audit_identity' and identity['anchor_sha256'] == 'c10b94507a190fc464ea9d5d33abc1f2199c3543ddc9be31573c97f85d2b14cd' and identity['milliseconds'] == 5000
        clocks = [row for row in rows if row['kind'] == 'anchor_clock']
        bases = [row for row in clocks if row['line'] == 45]
        assert len(bases) == 1
        deadline = bases[0]['value']+identity['milliseconds']/1000
        spawn = next(row for row in rows if row['kind'] == 'target_spawn')
        assert all(row['anchor_pid'] == spawn['anchor_pid'] for row in clocks) and spawn['pid'] != spawn['anchor_pid']
        polls = [row for row in rows if row['kind'] == 'target_poll']
        assert polls and all(row['pid'] == spawn['pid'] for row in polls)
        values = [row['value'] for row in rows if 'value' in row]
        assert all(type(value) is float and value > 0 for value in values) and values == sorted(values)
        completed = [row for row in polls if row['code'] is not None]
        assert completed and all(row['code'] == expected_code for row in completed)
        decisions = [row for row in clocks if row['line'] == 101]
        assert decisions
        if index == 0:
            result = json.loads((case/'retained-failure.json').read_text())
            assert result['error'] == 'Error: Observed compiler failed: deadline' and result['records'] == [] and len(result['failures']) == 1
            record = result['failures'][0]['record']
            assert completed[0]['value'] > deadline and decisions[-1]['value'] >= deadline
            assert completed[0]['sequence'] > decisions[-1]['sequence']
            assert not (case/'result.json').exists() and not (case/'0-frame.raw').exists()
        else:
            result = json.loads((case/'result.json').read_text())
            assert len(result['records']) == 1 and result['failures'] == []
            record = result['records'][0]['execution']
            assert completed[0]['value'] < deadline and all(row['value'] < deadline for row in decisions)
            expected = (case/'0-expected.raw').read_bytes()
            assert len(expected) == 16384 and hashlib.sha256(expected).hexdigest() == '13621c23ad70860d9eacd60f1a85dfee0b606fbcaea0e0f792745e7bff424461' and (case/'0-frame.raw').read_bytes() == expected
            assert not (case/'retained-failure.json').exists()
        assert record['pid'] == spawn['anchor_pid'] and record['emergencyClosed'] is False and record['privateAbortRequested'] is False
        report = record['report']
        assert report['drained'] is True and report['target_code'] == expected_code and report['failure'] == ('deadline' if index == 0 else None) and report['remaining_observed'] == 0
        assert json.loads((case/'outer-wait.json').read_text()) == {'code':1 if index == 0 else 0,'timeout':False}
        assert json.loads((case/'closure.json').read_text()) == {'liveWorkers':0,'busy':False,'closed':True,'revision':index}
        outcomes.append({'target_code':expected_code,'first_terminal_poll_minus_deadline':completed[0]['value']-deadline,'deadline_verdict':index == 0})
    return {'actual_build_jobs':2,'same_clock_outcomes':outcomes,'successful_frame_bytes':16384,'false_deadline_observed':False,'historical_completion_time_qualified':False}
