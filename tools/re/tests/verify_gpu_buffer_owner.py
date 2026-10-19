def _require(condition):
    if not condition:
        raise AssertionError('GPU lifecycle evidence rejected')

import base64, hashlib, json
from pathlib import Path

def verify(folder):
    e = Path(folder)

    def seal(root):
        m = json.loads((root / 'manifest.json').read_text())
        _require(set(m['files']) == {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p != root / 'manifest.json'})
        for (n, x) in m['files'].items():
            p = root / n
            _require(not Path(n).is_absolute() and '..' not in Path(n).parts and (not p.is_symlink()))
            b = p.read_bytes()
            _require(len(b) == x['bytes'] and hashlib.sha256(b).hexdigest() == x['sha256'])
    seal(e)
    seal(e / 'baseline')
    pred = json.loads((e / 'prediction.json').read_text())
    _require(pred['parent_manifest_sha256'] == '9cb67c04646592908039c9a3f0f04e62fac07a56af58f8ab196f92d20affa4ea' and pred['baseline_manifest_sha256'] == 'b1d713bfd982b3606f8cfb1c5e0d95615571f424c3e6bf207c0b0bc110ae7a0b')
    _require(hashlib.sha256((e / 'baseline/manifest.json').read_bytes()).hexdigest() == pred['baseline_manifest_sha256'])
    assessment = json.loads((e / 'baseline/assessment.json').read_text())
    _require(assessment['prediction_supported'] is False and assessment['acceptance'] is False)
    rea = json.loads((e / 'rea.json').read_text())
    _require(rea['closed'] is True and rea['identity']['package']['version'] == '6.2.0')

    def integer(x, v):
        _require(type(x) is int and x == v)
    total = 0
    for (isolated, root, key) in [(False, e / 'baseline', 'baseline'), (True, e, 'isolated')]:
        _require(json.loads((root / 'compile.json').read_text())['wait'] == 0)
        env = json.loads((root / 'environment.json').read_text())
        _require(env['machine'].strip() == 'arm64' and '26.6' in env['xcode'] and ('25F80' in env['sw_vers']))
        _require(rea[key]['subject']['digest']['sha256'] == env['helper_sha256'] and rea[key + 'Open']['result']['sha256'] == env['helper_sha256'] and (rea[key]['provider']['id'] == 'native-macos'))
        previous = None
        for i in range(2):
            _require(json.loads((root / f'wait-{i}.json').read_text()) == {'code': 0, 'timeout': False, 'stderr': ''})
            d = json.loads((root / f'result-{i}.json').read_text())
            integer(d['allocation_bytes'], 16384)
            _require(d['unified_memory'] is True and d['device'] == 'Apple M1')
            _require([x['mode'] for x in d['rows']] == ['cpu-only', 'retained-unencoded', 'retained-encoded', 'unretained-encoded'])
            raw = []
            for (mode, row) in enumerate(d['rows']):
                alive = not isolated or mode == 2
                _require(row['submitted'] is False and row['weak_buffer_alive_after_cpu_drop'] is alive)
                _require(row['weak_buffer_alive_after_pool_drain'] is False and row['weak_command_alive_after_pool_drain'] is False and (row['weak_command_alive_before_pool_drain'] is (mode != 0)))
                if mode == 0:
                    _require(row['retained_references'] is None and row['command_status'] is None)
                else:
                    _require(row['retained_references'] is (mode != 3))
                    integer(row['command_status'], 0)
                t = row['token_before']
                _require(type(t) is int and t > 0)
                integer(row['token_after_cpu_drop'], t if alive else 0)
                b = base64.b64decode(row['before'], validate=True)
                _require(b == bytes([92] * 16384))
                total += len(b)
                raw.append(b)
                if alive:
                    b = base64.b64decode(row['after'], validate=True)
                    _require(b == bytes([92] * 16384))
                    total += len(b)
                    raw.append(b)
                else:
                    _require(row['after'] is None)
            if previous is not None:
                _require(raw == previous)
            previous = raw
    _require(total == 425984)
    return {'complete_bytes': total, 'baseline_contradictions': 6, 'isolated_controls': 8}
