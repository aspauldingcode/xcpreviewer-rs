import hashlib
import json
from pathlib import Path

PIN = '48c73a15ac5720ec653271bc6ec523a090fb2bff4301f2308a9812faea4187b8'


def _require(condition):
    if not condition:
        raise AssertionError("Completion evidence rejected")


def verify(folder):
    evidence = Path(folder)
    manifest = json.loads((evidence/'manifest.json').read_text())
    actual = {str(p.relative_to(evidence)) for p in evidence.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    _require(set(manifest['files']) == actual)
    for name, expected in manifest['files'].items():
        _require(not Path(name).is_absolute() and '..' not in Path(name).parts)
        path = evidence/name
        _require(not path.is_symlink())
        payload = path.read_bytes()
        _require(len(payload) == expected['bytes'] and hashlib.sha256(payload).hexdigest() == expected['sha256'])
    _require(hashlib.sha256((evidence/'anchor.py').read_bytes()).hexdigest() == PIN)
    _require(json.loads((evidence/'slots.json').read_text()) == {'used':4,'limit':4})
    payload = bytes([0,1,2,255,10,42,99,128])
    outcomes = []
    errors = {'delayed-zero':None,'delayed-failure':'Error: Observed compiler failed: 43','late':'Error: Observed compiler failed: deadline','abort':'Error: Observed compiler aborted'}
    for mode, error in errors.items():
        root = evidence/mode
        result = json.loads((root/'result.json').read_text())
        record = result['record']; report = record['report']
        _require(result['mode'] == mode and result['error'] == error)
        _require(report['failure'] == ('deadline' if mode == 'late' else 'abort' if mode == 'abort' else None))
        _require(report['drained'] is True and report['remaining_observed'] == 0)
        _require(report['target_code'] == (43 if mode == 'delayed-failure' else 0))
        _require(record['emergencyClosed'] is False and record['privateAbortRequested'] == (mode == 'abort'))
        _require(record['signal'] == 'SIGKILL')
        _require((root/'owned.raw').read_bytes() == payload)
        for stream, expected in [('stdout',payload),('stderr',b'')]:
            _require(record[stream+'Bytes'] == len(expected))
            _require(record[stream+'Sha256'] == hashlib.sha256(expected).hexdigest())
            _require(record[stream] == expected.decode('utf8',errors='replace'))
        _require(json.loads((evidence/('wait-'+mode+'.json')).read_text()) == {'code':0,'stdout':'owned completion guard pass\n','stderr':'','timeout':False})
        rows = [json.loads(line) for line in (root/'deadline-audit.jsonl').read_text().splitlines()]
        _require(0 < len(rows) < 512 and [r['sequence'] for r in rows] == list(range(1,len(rows)+1)))
        _require(rows[0]['anchor_sha256'] == PIN and rows[0]['milliseconds'] == 1000)
        base = next(r for r in rows if r['kind'] == 'anchor_clock' and r['line'] == 45)
        deadline = base['value']+1
        spawn = next(r for r in rows if r['kind'] == 'target_spawn')
        _require(spawn['anchor_pid'] == record['pid'] and spawn['pid'] != record['pid'])
        polls = [r for r in rows if r['kind'] == 'target_poll' and r['code'] is not None]
        _require(polls and all(r['pid'] == spawn['pid'] and r['code'] == report['target_code'] for r in polls))
        terminal = polls[0]
        decisions = [r for r in rows if r['kind'] == 'anchor_clock' and r['line'] == 110]
        starts = [r for r in rows if r['kind'] == 'injected_delay_start']
        ends = [r for r in rows if r['kind'] == 'injected_delay_end']
        if mode.startswith('delayed-'):
            _require(len(starts) == len(ends) == 1 and decisions)
            _require(terminal['value'] < deadline and starts[0]['terminal_observed_at'] < deadline)
            _require(starts[0]['deadline'] == deadline)
            _require(terminal['sequence'] < starts[0]['sequence'] < ends[0]['sequence'] < decisions[0]['sequence'])
            _require(terminal['value'] <= starts[0]['value'] < deadline < ends[0]['value'] <= decisions[0]['value'])
        else:
            _require(starts == ends == [])
            if mode == 'late':
                _require(terminal['value'] >= deadline and any(r['value'] >= deadline for r in decisions))
            else:
                _require(not decisions and terminal['value'] < deadline)
        outcomes.append({'mode':mode,'target_wait_code':report['target_code'],'first_terminal_poll_minus_deadline':terminal['value']-deadline})
    return {'owned_peer_jobs':4,'native_compiler_builds':0,'controlled_payload_bytes':32,'outcomes':outcomes,'completion_guard_verified':True,'native_canvas_protocol_qualified':False}
