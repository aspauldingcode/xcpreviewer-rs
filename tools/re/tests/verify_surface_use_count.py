def _require(condition):
    if not condition:
        raise AssertionError('Surface lifecycle evidence rejected')

import hashlib, json
from pathlib import Path

def verify(folder):
    e = Path(folder)
    m = json.loads((e / 'manifest.json').read_text())
    _require(set(m['files']) == {str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name != 'manifest.json'})
    for (name, row) in m['files'].items():
        p = e / name
        _require(not Path(name).is_absolute() and '..' not in Path(name).parts and (not p.is_symlink()))
        b = p.read_bytes()
        _require(len(b) == row['bytes'] and hashlib.sha256(b).hexdigest() == row['sha256'])
    env = json.loads((e / 'environment.json').read_text())
    rea = json.loads((e / 'rea.json').read_text())
    _require(env['macos'] == '26.5.1' and env['build'] == '25F80')
    _require(env['binary_sha256'] == rea['target']['sha256'] == '205991b8c05c6cbae8c36f8623a7b2cec1f6ebe92062f35bb46dc7b2a8fe3187')
    _require(rea['target']['architecture'] == 'arm64' and rea['server']['version'] == '6.2.0')
    _require(json.loads((e / 'compile.json').read_text())['code'] == 0)
    for (mode, (w, h, stride, seed)) in enumerate([(17, 9, 128, 49), (13, 7, 128, 178)]):
        root = e / str(mode)
        d = json.loads((root / 'result.json').read_text())
        _require(json.loads((e / (str(mode) + '-wait.json')).read_text()) == {'code': 0, 'stdout': '', 'stderr': ''})
        _require([d[x] for x in ['mode', 'width', 'height', 'stride', 'seed', 'allocation']] == [mode, w, h, stride, seed, 16384])
        _require(d['same_id'] is True and d['initial_ref_status'] == d['release_status'] == d['final_send_refs'] == 0 and (d['final_ref_status'] == 15))
        _require(d['alias_only_count'] == 0 and d['alias_only_in_use'] is False)
        _require(d['states'] == [{'phase': phase, 'original_count': count, 'alias_count': count, 'original_in_use': True, 'alias_in_use': True} for (phase, count) in zip(['baseline', 'increment-original', 'increment-second', 'decrement-second', 'zero-with-right'], [0, 1, 2, 1, 0])])
        expected = bytearray([165] * 16384)
        for y in range(h):
            for x in range(w):
                for c in range(4):
                    expected[y * stride + x * 4 + c] = 255 if c == 3 else seed + x * 17 + y * 31 + c * 53 & 255
        for stage in ['baseline', 'zero', 'alias-only']:
            _require((root / (stage + '.raw')).read_bytes() == expected)
    return {'owned_native_jobs': 2, 'full_allocation_bytes': 98304, 'padding_bytes': 3216, 'allocation_tail_bytes': 92160, 'local_count_shared_across_aliases': True, 'zero_local_count_with_in_use_true': True, 'in_use_false_with_readable_alias': True, 'physical_reclamation_qualified': False, 'native_canvas_protocol_qualified': False}
