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
    assert config['rustcSha'] == '210df6794001b73ec3d453878707fa1e0bdcb63c427024a6e6574bbe5615a4da'
    assert config['observer']['sha256'] == '718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5'
    prediction = json.loads((evidence/'prediction.json').read_text())
    assert prediction == {'modes':['cancel-0','cancel-1','success-0','success-1'],'wait_codes':[-15,-15,0,0],'child_wait_qualified':True,'supervisor_integration_qualified':False,'native_canvas_qualified':False,'outer_seconds':30,'observation_seconds':2,'wait_seconds':3}
    assert json.loads((evidence/'slots.json').read_text()) == {'used':4,'limit':4}
    assert json.loads((evidence/'outer-wait.json').read_text()) == {'code':0,'stdout':'cancel-0 -15\ncancel-1 -15\nsuccess-0 0\nsuccess-1 0\n','stderr':''}
    pids = []
    for mode, code in zip(prediction['modes'],prediction['wait_codes']):
        root = evidence/mode
        result = json.loads((root/'result.json').read_text())
        assert result['mode'] == mode and result['wait_code'] == code and 0 < result['elapsed_seconds'] < 5
        source = ''.join('pub fn function_'+str(index)+'()->u64{'+str(index)+'}\n' for index in range(50000 if code else 1)).encode()
        assert (root/'input.rs').read_bytes() == source and result['source_bytes'] == len(source) and result['source_sha256'] == hashlib.sha256(source).hexdigest()
        assert result['command'][:7] == [config['rustc'],'--crate-name','owned_wait','--crate-type','lib','--emit','metadata']
        assert Path(result['command'][7]).parts[-2:] == (mode,'input.rs') and result['command'][8] == '-o' and Path(result['command'][9]).parts[-2:] == (mode,'output.rmeta')
        assert result['output_present'] is (code == 0) and (root/'output.rmeta').exists() is (code == 0)
        for stream in ['stdout','stderr']:
            assert (root/(stream+'.raw')).read_bytes() == b'' and result[stream+'_bytes'] == 0 and result[stream+'_sha256'] == hashlib.sha256(b'').hexdigest()
        if code:
            row = result['observation']
            assert row['pid'] == result['pid'] and row['parent'] == result['parent_pid'] and row['group'] == row['pid'] and row['state'] == 'L'
            assert row in result['rechecked'] and row['identity'][2] == config['rustc'] and type(row['identity'][0]) is int and row['identity'][0] > 0 and type(row['identity'][1]) is int and 0 <= row['identity'][1] < 1000000
        else:
            assert result['observation'] is None and result['rechecked'] is None
        pids.append(result['pid'])
    assert len(set(pids)) == 4
    return {'native_controls':4,'actual_rustc_wait_codes':[-15,-15,0,0],'controlled_source_bytes':sum((evidence/mode/'input.rs').stat().st_size for mode in prediction['modes']),'supervisor_integration_qualified':False}
