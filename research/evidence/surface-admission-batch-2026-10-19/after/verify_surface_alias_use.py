def _require(condition):
    if not condition:
        raise AssertionError('Surface lifecycle evidence rejected')

import hashlib, json
from pathlib import Path

def verify(folder):
    e = Path(folder)
    m = json.loads((e / 'manifest.json').read_text())
    _require(set(m['files']) == {str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name != 'manifest.json'})
    for (n, x) in m['files'].items():
        _require(not Path(n).is_absolute() and '..' not in Path(n).parts)
        p = e / n
        _require(not p.is_symlink())
        raw = p.read_bytes()
        _require(len(raw) == x['bytes'] and hashlib.sha256(raw).hexdigest() == x['sha256'])
    compile = json.loads((e / 'compile.json').read_text())
    _require(compile['code'] == 0 and compile['timeout'] is False)

    def expected(seed):
        raw = bytearray([seed]) * 16384
        raw[:1152] = bytes([165]) * 1152
        for y in range(9):
            for x in range(17):
                for c in range(4):
                    raw[y * 128 + x * 4 + c] = 255 if c == 3 else seed + x * 17 + y * 31 + c * 53 & 255
        return raw
    old = expected(49)
    count = 0
    pids = []
    all_frames = []
    expected_counts = [(3, 0), (3, 1), (3, 2), (3, 1), (2, 1), (2, 0), (1, 0)]
    for mode in ['repeat-0', 'repeat-1']:
        root = e / mode
        wait = json.loads((root / 'wait.json').read_text())
        _require(wait['code'] == 0 and wait['timeout'] is False and (wait['stderr'] == ''))
        row = json.loads(wait['stdout'])
        _require(type(row['pid']) is int and row['pid'] > 1 and (type(row['surface_id']) is int) and (row['surface_id'] > 0))
        pids.append(row['pid'])
        for (k, v) in {'allocation_bytes': 16384, 'stride': 128, 'resource_name_removed': True, 'all_cf_owners_released': True, 'balanced_use_calls': True, 'lookup_after_release': False}.items():
            _require(row[k] == v and type(row[k]) is type(v))
        _require(row['equal_refs'] == [False, False, False] and all((type(x) is bool for x in row['equal_refs'])))
        _require(len(row['samples']) == 7)
        frames = {}
        for (stage, (n, local)) in enumerate(expected_counts):
            sample = row['samples'][stage]
            _require(sample['stage'] == stage and type(sample['stage']) is int and (sample['local'] == [local] * n) and (sample['global'] == [int(local > 0)] * n) and all((type(x) is int for x in sample['local'] + sample['global'])))
            frames.update({f'stage-{stage}-alias-{i}.bin': old for i in range(n)})
        _require({p.name for p in root.glob('*.bin')} == set(frames))
        observed = {}
        for (name, expected_bytes) in frames.items():
            observed[name] = (root / name).read_bytes()
            _require(observed[name] == expected_bytes)
            count += 1
        all_frames.append(observed)
    _require(pids[0] != pids[1] and all_frames[0] == all_frames[1] and (count == 34))
    env = json.loads((e / 'environment.json').read_text())
    rea = json.loads((e / 'rea.json').read_text())
    _require(rea['open']['result']['sha256'] == rea['identity']['result']['sha256'] == env['helper_sha256'] == 'a6e459246b10526907d3bf72c9b5fa56830e5ff40f414d5e280b23141857f7a6' and rea['identity']['result']['architecture'] == 'arm64' and (rea['closed']['result'] is None))
    return {'allocations': count, 'full_allocation_bytes': count * 16384, 'padding_bytes': count * 540, 'tail_bytes': count * 15232, 'fresh_repeats': 2, 'distinct_cf_wrappers_per_helper': 3, 'physical_reclamation': False, 'canvas_protocol': False}
