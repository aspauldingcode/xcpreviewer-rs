def _require(condition):
    if not condition:
        raise AssertionError('Surface lifecycle evidence rejected')

import hashlib, json
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
    _require(json.loads((e / 'compile.json').read_text())['wait'] == 0)
    env = json.loads((e / 'environment.json').read_text())
    _require(env['machine'].strip() == 'arm64' and '26.6' in env['xcode'] and ('25F80' in env['sw_vers']))
    rea = json.loads((e / 'rea.json').read_text())
    _require(rea['closed'] is True and rea['identity']['package']['version'] == '6.2.0' and (rea['inspection']['provider']['id'] == 'native-macos'))
    _require(env['helper_sha256'] == rea['open']['result']['sha256'] == rea['inspection']['subject']['digest']['sha256'])
    _require(json.loads((e / 'prediction.json').read_text())['parent_manifest_sha256'] == 'd8500f8f4038a772748b22e68233a7316640fc3c079e1e5e1c14c02b3aa0c9a1')
    total = 0
    previous = None
    for mode in ['copy', 'move']:
        for i in range(2):
            f = e / (mode + '-' + str(i))
            _require(json.loads((f / 'wait.json').read_text()) == {'code': 0, 'timeout': False, 'stderr': ''})
            d = json.loads((f / 'result.json').read_text())
            _require(d['mode'] == mode)
            for (k, v) in [('peer_exit', 45), ('peer_signal', 0), ('width', 11), ('height', 6), ('seed', 33), ('stride', 128), ('allocation_bytes', 16384), ('queued_messages_before_drop', 1), ('sender_refs_after_send', 1 if mode == 'copy' else 0), ('replacement_refs', 1)]:
                _require(type(d[k]) is int and d[k] == v)
            _require(all((d[k] is True for k in ['final_names_removed', 'peer_endpoints_dead', 'audit_peers_verified', 'rendezvous_removed'])) and d['receiver_imported'] is False and (d['completion_accepted'] is False))
            _require(all((type(d[k]) is int and d[k] > 1 for k in ['sender_pid', 'receiver_pid'])) and d['sender_pid'] != d['receiver_pid'])
            expected = bytearray([165] * 16384)
            for y in range(6):
                for x in range(11):
                    for c in range(4):
                        expected[y * 128 + x * 4 + c] = 255 if c == 3 else 33 + x * 17 + y * 31 + c * 53 & 255
            mutated = bytearray(expected)
            mutated[0] ^= 90
            raw = []
            for (n, wanted) in [('before.bin', expected), ('after-drop.bin', expected), ('port-only.bin', mutated)]:
                b = (f / n).read_bytes()
                _require(b == wanted)
                total += len(b)
                raw.append(b)
            if previous is not None:
                _require(previous == raw)
            previous = raw
    _require(total == 196608)
    return {'complete_bytes': total, 'native_waits': 4, 'queued_discard_controls': 4}
