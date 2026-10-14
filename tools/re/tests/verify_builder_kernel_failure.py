import hashlib
import json
import os
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
    assert b'ERR_ASSERTION' in (evidence/'control.stderr').read_bytes() and not (evidence/'result.json').exists()
    result = json.loads((evidence/'retained-failure.json').read_text())
    assert result['qualified'] is False and result['retryUnchanged'] is False and len(result['records']) == 1 and len(result['failures']) == 2
    assert [failure['error'] for failure in result['failures']] == ['Error: Observed compiler aborted','Error: Observed compiler failed: deadline']
    for failure, kind in zip(result['failures'],['abort','deadline']):
        record = failure['record']
        assert record['emergencyClosed'] is False and record['signal'] == 'SIGKILL'
        assert record['privateAbortRequested'] is (kind == 'abort')
        report = record['report']
        assert report['failure'] == kind and report['target_code'] == -15 and report['drained'] is True and report['remaining_observed'] == 0
    child = result['trigger']['compiler']
    assert any(child == row for batch in result['observations'] for row in batch)
    assert child['group'] == result['failures'][0]['record']['pid'] and child['state'] == 'L'
    config = json.loads((evidence/'config.json').read_text())
    assert child['identity'][2] == config['rustc'] and child['identity'][0] > 0 and 0 <= child['identity'][1] < 1000000
    registered = {'registered':True,'pid':child['pid'],'seconds':child['identity'][0],'micros':child['identity'][1]}
    assert result['trigger']['registration'] == registered
    watcher = json.loads((evidence/'compiler-kernel-wait.json').read_text())
    assert watcher['code'] == 0 and watcher['signal'] is None and watcher['stderr'] == ''
    rows = [json.loads(line) for line in watcher['stdout'].splitlines()]
    assert rows == [registered,{'pid':child['pid'],'raw_status':15,'exited':False,'exit_code':-1,'flags':32821,'fflags':2214592512}]
    assert os.WIFSIGNALED(rows[1]['raw_status']) and os.WTERMSIG(rows[1]['raw_status']) == 15
    expected = (evidence/'0-expected.raw').read_bytes()
    assert len(expected) == 16384 and hashlib.sha256(expected).hexdigest() == '13621c23ad70860d9eacd60f1a85dfee0b606fbcaea0e0f792745e7bff424461'
    assert (evidence/'baseline.raw').read_bytes() == (evidence/'retained-at-cancel.raw').read_bytes() == expected
    assert not (evidence/'recovered.raw').exists()
    events = result['events']
    assert [(row['kind'],row.get('generation')) for row in events] == [('observed',1),('published',1),('observed',2),('observed',3),('rejected',2),('rejected',3)]
    assert events[4]['error'] == 'Error: Observed compiler aborted' and events[5]['error'] == 'Error: Observed compiler failed: deadline'
    stages = list((evidence/'builds').glob('build-*'))
    assert len(stages) == 3 and sum((stage/'result/receipt.json').exists() for stage in stages) == 1
    assert {hashlib.sha256((stage/'source.swift').read_bytes()).hexdigest() for stage in stages} == {'37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8','201ed0fc3d92c2896af028f2c7961712b4a183f55e35f36266eb393d985bd953','d11ab052939b2b5b4b88e58fb0ee1e210772d2a756083bfd6f9d8f34452818cc'}
    baseline = result['records'][0]
    base = evidence/'builds'/baseline['stage']
    receipt = baseline['receipt']
    assert receipt == json.loads((base/'result/receipt.json').read_text()) and receipt['module_sha256'] == hashlib.sha256((base/'result/view.wasm').read_bytes()).hexdigest()
    assert receipt['source_sha256'] == hashlib.sha256((base/'source.swift').read_bytes()).hexdigest() and receipt['rustc_sha256'] == config['rustcSha']
    assert baseline['execution']['report']['drained'] is True and baseline['execution']['report']['target_code'] == 0
    assert json.loads((evidence/'closure.json').read_text()) == {'liveWorkers':0,'busy':False,'closed':True,'revision':1,'loopClosed':True,'building':False,'timers':0}
    assert json.loads((evidence/'prediction.json').read_text()) == {'owned_build_budget':3,'compiler_kernel_raw_status':15,'compiler_parent_wait_observed':False,'supersession_registration_required':True,'outer_seconds':30}
    return {'fresh_build_jobs':3,'compiler_kernel_signal':15,'baseline_retained_bytes':32768,'recovery_qualified':False,'compiler_parent_wait_qualified':False}
