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
        p = e / n
        _require(not Path(n).is_absolute() and '..' not in Path(n).parts and (not p.is_symlink()))
        b = p.read_bytes()
        _require(len(b) == x['bytes'] and hashlib.sha256(b).hexdigest() == x['sha256'])
    _require(json.loads((e / 'compile.json').read_text())['wait'] == 0)
    pred = json.loads((e / 'prediction.json').read_text())
    _require(pred['parent_manifest_sha256'] == '0841c787c1afff6c0da6833cb5dd78dd5f82ed02c2669e948ae09a71109c615c' and pred['subprocess_deadline_seconds'] == 15)
    env = json.loads((e / 'environment.json').read_text())
    _require(env['machine'].strip() == 'arm64' and '26.6' in env['xcode'] and ('25F80' in env['sw_vers']))
    rea = json.loads((e / 'rea.json').read_text())
    _require(rea['inspection']['subject']['digest']['sha256'] == env['helper_sha256'] and rea['inspection']['provider']['id'] == 'native-macos' and (rea['open']['result']['sha256'] == env['helper_sha256']))
    _require(rea['closed'] is True and rea['identity']['server_identity']['package']['version'] == '6.2.0')

    def integer(x, v):
        _require(type(x) is int and x == v)
    raw_previous = None
    all_bytes = 0
    for i in range(2):
        _require(json.loads((e / f'wait-{i}.json').read_text()) == {'code': 0, 'timeout': False, 'stderr': ''})
        d = json.loads((e / f'result-{i}.json').read_text())
        integer(d['allocation_bytes'], 16384)
        integer(d['row'], 256)
        integer(d['width_bytes'], 44)
        integer(d['height'], 6)
        integer(d['wait_ns'], 20000000)
        integer(d['completion_ns'], 5000000000)
        _require(d['unified_memory'] is True and d['device'] == 'Apple M1')
        _require([x['mode'] for x in d['rows']] == ['encoded-uncommitted', 'committed-timeout'])
        raw = []
        for (committed, row) in enumerate(d['rows']):
            for k in ['retained_references', 'error_absent', 'weak_alive_after_cpu_drop', 'weak_alive_before_pool_drain']:
                _require(row[k] is True)
            for k in ['weak_buffer_alive_after_pool_drain', 'weak_command_alive_after_pool_drain']:
                _require(row[k] is False)
            t = row['token_before']
            _require(type(t) is int and t > 0 and (row['token_after_cpu_drop'] == t) and (row['token_before_pool_drain'] == t))
            integer(row['callback_count'], committed)
            integer(row['status'], 4 if committed else 0)
            integer(row['event_after'], committed)
            if committed:
                _require(row['timeout_observed'] is True and row['weak_alive_pending'] is True)
                integer(row['callbacks_before_release'], 0)
                integer(row['event_before_release'], 0)
                _require(type(row['status_before_release']) is int and row['status_before_release'] in [2, 3])
            before = bytes([92] * 16384)
            after = bytearray(before)
            if committed:
                for y in range(6):
                    after[y * 256:y * 256 + 44] = bytes([119] * 44)
            for (key, wanted) in [('before', before), ('after', bytes(after))]:
                b = base64.b64decode(row[key], validate=True)
                _require(b == wanted)
                raw.append(b)
                all_bytes += len(b)
        if raw_previous is not None:
            _require(raw == raw_previous)
        raw_previous = raw
    _require(all_bytes == 131072)
    return {'complete_bytes': all_bytes, 'repetitions': 2, 'post_pool_weak_nil_cases': 4}
