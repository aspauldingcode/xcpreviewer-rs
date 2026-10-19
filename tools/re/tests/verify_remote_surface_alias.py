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
    wait = json.loads((e / 'wait.json').read_text())
    _require(wait['code'] == 0 and wait['timeout'] is False and (wait['stderr'] == ''))
    rows = [json.loads(line) for line in wait['stdout'].splitlines()]
    _require(len(rows) == 2)

    def expected(seed):
        raw = bytearray([seed]) * 16384
        raw[:1152] = bytes([165]) * 1152
        for y in range(9):
            for x in range(17):
                for c in range(4):
                    raw[y * 128 + x * 4 + c] = 255 if c == 3 else seed + x * 17 + y * 31 + c * 53 & 255
        return raw
    (old, new) = (expected(49), expected(50))
    count = 0
    parents = []
    peers = []
    for (row, mode) in zip(rows, ['clean', 'abrupt']):
        root = e / mode
        peer = json.loads((root / 'peer.json').read_text())
        _require(type(row['old_id']) is int and row['old_id'] > 0)
        for (k, v) in {'mode': mode, 'allocation_bytes': 16384, 'stride': 128, 'parent_cf_owner_released': True, 'parent_surface_right_removed': True, 'held_creations': 64, 'global_lookup_while_peer': True, 'peer_exit': 0 if mode == 'clean' else -1, 'peer_signal': 0 if mode == 'clean' else 9, 'lookup_after_peer': False, 'attempts_after_peer': 1, 'matched_after_peer': True, 'rendezvous_removed': True, 'peer_endpoint_name_removed': True}.items():
            _require(row[k] == v and type(row[k]) is type(v))
        _require(type(row['sender_pid']) is int and type(row['receiver_pid']) is int and (row['sender_pid'] > 1) and (row['receiver_pid'] > 1) and (row['sender_pid'] != row['receiver_pid']))
        parents.append(row['sender_pid'])
        peers.append(row['receiver_pid'])
        for (k, v) in {'pid': row['receiver_pid'], 'parent': row['sender_pid'], 'surface_id': row['old_id'], 'audit_peer_verified': True, 'imported_right_released': True, 'local_resource_name_removed': True, 'cf_alias_retained': True}.items():
            _require(peer[k] == v and type(peer[k]) is type(v))
        _require(len(row['held_ids']) == 64 and all((type(x) is int and x > 0 and (x != row['old_id']) for x in row['held_ids'])))
        _require(row['after_ids'] == [row['old_id']])
        frames = {n: old for n in ['initial.bin', 'peer-before.bin', 'peer-after-churn.bin', 'global-while-peer.bin']}
        frames.update({f'held-candidate-{i:03d}.bin': new for i in range(64)})
        frames.update({'after-candidate-000.bin': new, 'stale-lookup.bin': new})
        _require({p.name for p in root.glob('*.bin')} == set(frames))
        for (name, expected_bytes) in frames.items():
            _require((root / name).read_bytes() == expected_bytes)
            count += 1
    _require(parents[0] == parents[1] and len(set(peers)) == 2)
    env = json.loads((e / 'environment.json').read_text())
    rea = json.loads((e / 'rea.json').read_text())
    _require(rea['open']['result']['sha256'] == rea['identity']['result']['sha256'] == env['helper_sha256'] == '8ecdeb3660a706220f8107e44a42f673a7a3705b60df3757e6297767f8cd5de9' and rea['identity']['result']['architecture'] == 'arm64' and (rea['closed']['result'] is None))
    _require(count == 140)
    return {'allocations': count, 'full_allocation_bytes': count * 16384, 'padding_bytes': count * 540, 'tail_bytes': count * 15232, 'remote_cf_alias_controls': 2, 'physical_reclamation': False, 'canvas_protocol': False}
