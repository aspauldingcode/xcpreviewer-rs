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
    assert json.loads((evidence/'outer-wait.json').read_text()) == {'code':1,'timeout':False}
    failure = json.loads((evidence/'retained-failure.json').read_text())
    assert failure['qualified'] is False and failure['retryUnchanged'] is False and failure['records'] == [] and len(failure['failures']) == 1 and failure['trigger'] is None
    record = failure['failures'][0]['record']
    report = record['report']
    assert failure['failures'][0]['error'] == 'Error: Observed compiler failed: deadline'
    assert report['drained'] is True and report['failure'] == 'deadline' and report['target_code'] == 0 and report['remaining_observed'] == 0
    assert record['emergencyClosed'] is False and record['privateAbortRequested'] is False and record['signal'] == 'SIGKILL'
    assert [(row['kind'],row.get('generation')) for row in failure['events']] == [('observed',1),('rejected',1)]
    assert not (evidence/'result.json').exists() and not (evidence/'baseline.raw').exists() and not (evidence/'compiler-kernel-wait.json').exists()
    stages = list((evidence/'builds').glob('build-*'))
    assert len(stages) == 1
    stage = stages[0]
    assert json.loads((stage/'failure.json').read_text()) == failure['failures'][0]
    receipt = json.loads((stage/'result/receipt.json').read_text())
    assert json.loads(record['stdout']) == receipt
    raw = record['stdout'].encode()
    assert len(raw) == record['stdoutBytes'] == 821 and hashlib.sha256(raw).hexdigest() == record['stdoutSha256']
    assert record['stderr'] == '' and record['stderrBytes'] == 0 and record['stderrSha256'] == hashlib.sha256(b'').hexdigest()
    assert receipt['source_sha256'] == hashlib.sha256((stage/'source.swift').read_bytes()).hexdigest() == '37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8'
    module = (stage/'result/view.wasm').read_bytes()
    assert len(module) == 17011 and hashlib.sha256(module).hexdigest() == receipt['module_sha256'] == '65c37c6d904ed43948d649da11d79932548b54ad8c0e10533e6d8f9d81ec0235'
    rows = [json.loads(line) for line in (stage/'cli-phases.jsonl').read_text().splitlines()]
    assert [row['phase'] for row in rows] == ['source_validated','compiler_identity_validated','snapshot_validated','generated_source_written','compiler_wait_completed','postbuild_identity_validated']
    assert [row['line'] for row in rows] == [19,21,23,28,30,32]
    assert len({row['pid'] for row in rows}) == 1 and rows[0]['pid'] > 0
    assert all(row['cli_sha256'] == 'd49ba1209f4a2545250c34322414b7f92f50435f110220433cfd33e83fc00c31' and 0 <= row['elapsed_seconds'] < 5 for row in rows)
    assert [row['elapsed_seconds'] for row in rows] == sorted(row['elapsed_seconds'] for row in rows)
    assert json.loads((evidence/'closure.json').read_text()) == {'liveWorkers':0,'busy':False,'closed':True,'revision':0,'loopClosed':True,'building':False,'timers':0}
    return {'actual_build_jobs':1,'declared_build_limit':3,'unused_build_slots':2,'compiler_cli_wait_code':0,'deadline_verdict_retained':True,'published_frames':0,'retained_module_bytes':17011,'recovery_qualified':False,'completion_before_deadline_qualified':False}
