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
    config = json.loads((evidence/'config.json').read_text())
    pin = '7d5588c16d38123c2dbe4e1b33ed482eaa74e424b7f5776df7ba2d2792e86828'
    assert config['toolchainPin'] == pin
    assert json.loads((evidence/'prediction.json').read_text()) == {'snapshot_controls':2,'compiler_builds':0,'pin':pin,'outer_seconds':30,'query_seconds':3,'historical_deadline_cause_qualified':False}
    rea = json.loads((evidence/'rea-status.json').read_text())
    assert rea['target']['architecture'] == 'arm64' and rea['target']['sha256'] == config['rustcSha'] == '210df6794001b73ec3d453878707fa1e0bdcb63c427024a6e6574bbe5615a4da'
    assert rea['server']['version'] == '6.2.0'
    durations = []
    for index in range(2):
        result = json.loads((evidence/('snapshot-'+str(index)+'.json')).read_text())
        identity = result['identity']
        canonical = json.dumps(identity,sort_keys=True,separators=(',',':')).encode()
        assert hashlib.sha256(canonical).hexdigest() == result['digest'] == pin
        assert identity['compiler'] == config['rustc'] and identity['compiler_file']['sha256'] == config['rustcSha']
        duration = result['elapsed_seconds']
        assert type(duration) is float and 0 < duration < 1
        durations.append(duration)
        queries = result['queries']
        expected_commands = [[config['rustc'],'--target','wasm32-wasip1','--print','target-libdir'],[config['rustc'],'--print','sysroot'],[config['rustc'],'-vV']]
        expected_output = [identity['target_libdir'],str(Path(config['rustc']).parents[1]),identity['compiler_version']]
        assert len(queries) == 3
        for query, command, output in zip(queries,expected_commands,expected_output):
            raw = (output+'\n').encode()
            assert query['command'] == command and query['wait_code'] == 0 and 0 < query['elapsed_seconds'] <= duration
            assert query['stdout_bytes'] == len(raw) and query['stdout_sha256'] == hashlib.sha256(raw).hexdigest()
            assert query['stderr_bytes'] == 0 and query['stderr_sha256'] == hashlib.sha256(b'').hexdigest()
        host = next(line[6:] for line in identity['compiler_version'].splitlines() if line.startswith('host: '))
        expected_files = {str(Path(identity['target_libdir'])/name):item for name,item in identity['target_files'].items()}
        expected_files.update({str(Path(config['rustc']).parents[1]/'lib/rustlib'/host/'bin'/name):item for name,item in identity['linkers'].items()})
        expected_files[config['rustc']] = identity['compiler_file']
        assert len(result['files']) == len(expected_files) == 61
        assert {item['path']:item['identity'] for item in result['files']} == expected_files
        assert all(0 <= item['elapsed_seconds'] <= duration for item in result['files'])
        assert sum(item['identity']['bytes'] for item in result['files']) == 233810837
    outer = json.loads((evidence/'outer-wait.json').read_text())
    assert outer['code'] == 0 and outer['stderr'] == ''
    return {'snapshot_controls':2,'query_wait_codes':[0]*6,'inventoried_bytes':467621674,'durations_seconds':durations,'historical_deadline_cause_qualified':False}
