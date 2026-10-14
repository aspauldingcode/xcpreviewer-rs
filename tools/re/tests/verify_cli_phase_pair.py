import hashlib
import json
from pathlib import Path

PIN = 'd49ba1209f4a2545250c34322414b7f92f50435f110220433cfd33e83fc00c31'
PHASES = ['source_validated','compiler_identity_validated','snapshot_validated','generated_source_written','compiler_wait_completed','postbuild_identity_validated']


def sealed(evidence):
    manifest = json.loads((evidence/'manifest.json').read_text())
    assert set(manifest['files']) == {str(path.relative_to(evidence)) for path in evidence.rglob('*') if path.is_file() and path.name != 'manifest.json'}
    for name, expected in manifest['files'].items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        payload = (evidence/name).read_bytes()
        assert not (evidence/name).is_symlink() and len(payload) == expected['bytes'] and hashlib.sha256(payload).hexdigest() == expected['sha256']


def verify(first, second):
    first, second = Path(first), Path(second)
    for evidence in [first,second]: sealed(evidence)
    assert hashlib.sha256((first/'cli.py').read_bytes()).hexdigest() == PIN
    budget = json.loads((second/'budget.json').read_text())
    assert budget == {'prior_builds':1,'this_builds':1,'shared_limit':2,'prior_manifest_sha256':'405d1222de1b7668d3f451bee2098b8b8d8e65bfb171f3543fb1f6ee4ae312a8','changed_factor':'trace starts after module imports','same_source':True}
    modules = []
    for evidence, count in [(first,5),(second,6)]:
        stages = list((evidence/'builds').glob('build-*'))
        assert len(stages) == 1
        stage = stages[0]
        source = (stage/'source.swift').read_bytes()
        assert hashlib.sha256(source).hexdigest() == '37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8'
        rows = [json.loads(line) for line in (stage/'cli-phases.jsonl').read_text().splitlines()]
        assert [row['phase'] for row in rows] == PHASES[:count]
        assert [row['line'] for row in rows] == [19,21,23,28,30,32][:count]
        assert len({row['pid'] for row in rows}) == 1 and all(type(row['pid']) is int and row['pid'] > 0 and row['cli_sha256'] == PIN for row in rows)
        times = [row['elapsed_seconds'] for row in rows]
        assert all(type(value) is float and 0 <= value < 5 for value in times) and times == sorted(times)
        diagnostics = (stage/'result/compile.stderr').read_bytes()
        assert len(diagnostics) == 1288 and hashlib.sha256(diagnostics).hexdigest() == '19db9ffbcb1885113579c897193ed8051fc9132e8b8d773bf2e1ee389fca1d3d'
        modules.append((stage/'result/view.wasm').read_bytes())
        outer = json.loads((evidence/'outer-wait.json').read_text())
        if count == 5:
            assert outer == {'code':1,'timeout':False} and not (evidence/'result.json').exists() and not (stage/'result/receipt.json').exists()
            result = json.loads((evidence/'retained-failure.json').read_text())
            assert result['error'] == 'Error: Observed compiler failed: deadline' and result['records'] == [] and len(result['failures']) == 1
            report = result['failures'][0]['record']['report']
            assert report['failure'] == 'deadline' and report['target_code'] == -15 and report['drained'] is True
            assert json.loads((evidence/'closure.json').read_text()) == {'liveWorkers':0,'busy':False,'closed':True,'revision':0}
        else:
            assert outer == {'code':0,'timeout':False} and (evidence/'control.stderr').read_bytes() == b'' and not (evidence/'retained-failure.json').exists()
            result = json.loads((evidence/'result.json').read_text())
            assert len(result['records']) == 1 and result['failures'] == []
            record = result['records'][0]
            receipt = json.loads((stage/'result/receipt.json').read_text())
            assert receipt == record['receipt'] and receipt['module_sha256'] == hashlib.sha256(modules[-1]).hexdigest() and receipt['source_sha256'] == hashlib.sha256(source).hexdigest()
            report = record['execution']['report']
            assert report['failure'] is None and report['target_code'] == 0 and report['drained'] is True
            expected = (evidence/'0-expected.raw').read_bytes()
            assert len(expected) == 16384 and hashlib.sha256(expected).hexdigest() == '13621c23ad70860d9eacd60f1a85dfee0b606fbcaea0e0f792745e7bff424461'
            assert (evidence/'0-frame.raw').read_bytes() == expected
            assert json.loads((evidence/'closure.json').read_text()) == {'liveWorkers':0,'busy':False,'closed':True,'revision':1}
    assert modules[0] == modules[1]
    return {'fresh_build_jobs':2,'first_deadline_retained':True,'optimized_build_qualified':True,'retained_frame_bytes':16384,'module_bytes_equal':len(modules[0]),'historical_deadline_cause_qualified':False}
