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
    edited = bytearray(old)
    for offset in [0, 68, 16383]:
        edited[offset] ^= 1
    wait = json.loads((e / 'wait.json').read_text())
    _require(wait['code'] == 0 and wait['timeout'] is False and (wait['stderr'] == ''))
    rows = [json.loads(line) for line in wait['stdout'].splitlines()]
    _require(len(rows) == 2)
    count = 0
    parents = []
    peers = []
    all_frames = []
    for (row, mode) in zip(rows, ['repeat-0', 'repeat-1']):
        root = e / mode
        peer = json.loads((root / 'peer.json').read_text())
        _require(type(row['surface_id']) is int and row['surface_id'] > 0)
        for (k, v) in {'allocation_bytes': 16384, 'stride': 128, 'resource_names_removed': True, 'parent_cf_released': True, 'peer_exit': 0, 'peer_signal': 0, 'rendezvous_removed': True, 'peer_endpoint_name_removed': True, 'lookup_after_release': False, 'initial_seed': 1, 'lock_seed': 2, 'unlock_seed': 2, 'restore_lock_seed': 3, 'restore_unlock_seed': 3}.items():
            _require(row[k] == v and type(row[k]) is type(v))
        _require(type(row['sender_pid']) is int and type(row['receiver_pid']) is int and (row['sender_pid'] > 1) and (row['receiver_pid'] > 1) and (row['sender_pid'] != row['receiver_pid']))
        parents.append(row['sender_pid'])
        peers.append(row['receiver_pid'])
        for (k, v) in {'pid': row['receiver_pid'], 'parent': row['sender_pid'], 'surface_id': row['surface_id'], 'audit_peer_verified': True, 'imported_right_released': True, 'local_resource_name_removed': True, 'cf_alias_released': True}.items():
            _require(peer[k] == v and type(peer[k]) is type(v))
        _require(len(peer['observations']) == 5)
        for (stage, seed) in enumerate([1, 2, 2, 2, 3]):
            sample = peer['observations'][stage]
            for (k, v) in {'stage': stage, 'before': seed, 'lock_seed': seed, 'unlock_seed': seed, 'after': seed, 'lock_code': 0, 'unlock_code': 0}.items():
                _require(sample[k] == v and type(sample[k]) is type(v))
        frames = {n: old for n in ['parent-initial.bin', 'parent-locked-before.bin', 'parent-restored.bin', 'peer-stage-0.bin', 'peer-stage-1.bin', 'peer-stage-4.bin']}
        frames.update({n: edited for n in ['parent-locked-after.bin', 'parent-after-unlock.bin', 'peer-stage-2.bin', 'peer-stage-3.bin']})
        _require({p.name for p in root.glob('*.bin')} == set(frames))
        observed = {}
        for (name, expected_bytes) in frames.items():
            observed[name] = (root / name).read_bytes()
            _require(observed[name] == expected_bytes)
            count += 1
        all_frames.append(observed)
    _require(parents[0] == parents[1] and len(set(peers)) == 2 and (all_frames[0] == all_frames[1]) and (count == 20))
    env = json.loads((e / 'environment.json').read_text())
    rea = json.loads((e / 'rea.json').read_text())
    _require(rea['open']['result']['sha256'] == rea['identity']['result']['sha256'] == env['helper_sha256'] == '3b40ed6cdb04844c701406e25ea8f0fc34ea8548535c28cf245ae68066e8a836' and rea['identity']['result']['architecture'] == 'arm64' and (rea['closed']['result'] is None))
    return {'allocations': count, 'full_allocation_bytes': count * 16384, 'padding_bytes': count * 540, 'tail_bytes': count * 15232, 'remote_peers': 2, 'held_write_interval_read_controls': 4, 'canvas_completion': False, 'arbitrary_concurrent_access': False}
