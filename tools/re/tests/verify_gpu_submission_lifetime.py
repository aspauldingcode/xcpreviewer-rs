def _require(condition):
    if not condition:
        raise AssertionError('GPU lifecycle evidence rejected')

import base64, hashlib, json
from pathlib import Path

def verify(folder):
    e = Path(folder)
    m = json.loads((e / 'manifest.json').read_text())
    _require(set(m['files']) == {str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p != e / 'manifest.json'})
    for (n, x) in m['files'].items():
        _require(not Path(n).is_absolute() and '..' not in Path(n).parts)
        p = e / n
        _require(not p.is_symlink())
        b = p.read_bytes()
        _require(len(b) == x['bytes'] and hashlib.sha256(b).hexdigest() == x['sha256'])
    _require(json.loads((e / 'baseline/assessment.json').read_text())['prediction_supported'] is False)
    _require(json.loads((e / 'sandbox-failure/assessment.json').read_text())['acceptance'] is False)
    _require(json.loads((e / 'sandbox-failure/wait-0.json').read_text()) == {'code': 2, 'timeout': False, 'stderr': 'check failed line 9\n'})
    _require((e / 'sandbox-failure/result-0.json').read_bytes() == b'')
    _require(json.loads((e / 'prediction.json').read_text())['parent_manifest_sha256'] == '7010b2175304947e02a515d44d895e02487dbc512da04a0ab7b6c3aad708db63')
    rea = json.loads((e / 'rea.json').read_text())
    _require(rea['closed'] is True and rea['identity']['package']['version'] == '6.2.0')

    def integer(x, v):
        _require(type(x) is int and x == v)
    expected = bytearray([92] * 16384)
    for y in range(6):
        expected[y * 256:y * 256 + 44] = bytes([119] * 44)
    total = 0
    for (root, inspect, opened, refined) in [(e / 'baseline', 'baseline', 'baselineOpen', False), (e, 'inspection', 'open', True)]:
        _require(json.loads((root / 'compile.json').read_text())['wait'] == 0)
        env = json.loads((root / 'environment.json').read_text())
        _require(env['machine'].strip() == 'arm64' and '26.6' in env['xcode'] and ('25F80' in env['sw_vers']))
        _require(rea[inspect]['subject']['digest']['sha256'] == env['helper_sha256'] == rea[opened]['result']['sha256'] and rea[inspect]['provider']['id'] == 'native-macos')
        for i in range(2):
            _require(json.loads((root / f'wait-{i}.json').read_text()) == {'code': 0, 'timeout': False, 'stderr': ''})
            d = json.loads((root / f'result-{i}.json').read_text())
            integer(d['allocation_bytes'], 16384)
            _require(d['device'] == 'Apple M1' and d['unified_memory'] is True)
            _require([x['mode'] for x in d['rows']] == ['encoded-uncommitted', 'committed-timeout'])
            for (mode, row) in enumerate(d['rows']):
                _require(row['retained_references'] is True and row['submitted'] is bool(mode))
                _require(row['weak_buffer_after_construction_pool'] is bool(mode) and row['weak_command_after_construction_pool'] is bool(mode))
                _require(row['weak_buffer_after_queue_pool'] is False and type(row['weak_command_after_queue_pool']) is bool)
                integer(row['callbacks_before_release'], 0 if mode else 1)
                integer(row['callbacks_after_release'], 1)
                integer(row['event_before_release'], 0)
                integer(row['event_after_release'], mode)
                token = row['token_before']
                _require(type(token) is int and token > 0)
                b = base64.b64decode(row['before'], validate=True)
                _require(b == bytes([92] * 16384))
                total += len(b)
                if mode:
                    _require(row['bounded_wait_timed_out'] is True)
                    integer(row['completion_status'], 4)
                    integer(row['token_in_callback'], token)
                    b = base64.b64decode(row['after'], validate=True)
                    _require(b == expected)
                    total += len(b)
                else:
                    _require(row['bounded_wait_timed_out'] is None and row['after'] is None)
                    integer(row['token_in_callback'], 0)
                    if refined:
                        integer(row['completion_status'], 0)
                    else:
                        _require(row['completion_status'] is None)
    _require(total == 196608)
    return {'complete_bytes': total, 'native_waits': 4, 'destruction_callbacks': 4}
