def _require(condition):
    if not condition:
        raise AssertionError('Partial-right evidence admission rejected')

import hashlib
import json
from pathlib import Path

def verify(folder):
    e = Path(folder)
    manifest = json.loads((e / 'manifest.json').read_text())
    _require(set(manifest['files']) == {str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name != 'manifest.json'})
    for (name, item) in manifest['files'].items():
        _require(not Path(name).is_absolute() and '..' not in Path(name).parts)
        p = e / name
        raw = p.read_bytes()
        _require(not p.is_symlink() and len(raw) == item['bytes'] and (hashlib.sha256(raw).hexdigest() == item['sha256']))
    _require(json.loads((e / 'slots.json').read_text()) == {'used': 2, 'limit': 2})
    _require(type(json.loads((e / 'compile-wait.json').read_text())['code']) is int)
    _require(json.loads((e / 'compile-wait.json').read_text()) == {'code': 0})
    identity = json.loads((e / 'identity.json').read_text())
    rea = json.loads((e / 'current-rea.json').read_text())
    _require(identity['sha256'] == rea['target']['sha256'] == '30302e9fae7108856afb51a29b821ebd057db0e291967605aea72a7e10adf5c4')
    _require(rea['target']['architecture'] == 'arm64' and rea['server']['version'] == '6.2.0')
    _require(identity['owned_case_limit'] == 2 and identity['private_capture_bridge_available'] is False)
    expected = bytearray([165] * 16384)
    for y in range(9):
        for x in range(17):
            for c in range(4):
                expected[y * 128 + x * 4 + c] = 255 if c == 3 else 49 + x * 17 + y * 31 + c * 53 & 255
    pids = []
    for mode in ['copy', 'move']:
        root = e / mode
        move = mode == 'move'
        _require(type(json.loads((root / 'wait.json').read_text())['code']) is int and json.loads((root / 'wait.json').read_text())['timeout'] is False)
        _require(json.loads((root / 'wait.json').read_text()) == {'code': 0, 'timeout': False})
        _require((root / 'stderr').read_bytes() == b'')
        rows = [json.loads(line) for line in (root / 'stdout.jsonl').read_text().splitlines()]
        _require(len(rows) == 1)
        r = rows[0]
        _require(all(type(r[key]) is int for key in ['pid', 'send_code', 'invalid_right_constant', 'original_name', 'returned_name', 'second_name', 'first_disposition', 'second_disposition', 'remote_type', 'before_original', 'before_returned', 'before_endpoint', 'after_original', 'after_returned', 'after_endpoint', 'invalid_type_before', 'invalid_query_after', 'invalid_type_after', 'empty_receive_code', 'remaining_send_refs', 'stride', 'allocation_bytes']))
        _require(r['move'] is move and r['pid'] > 0)
        pids.append(r['pid'])
        _require(type(r['original_name']) is int and r['original_name'] > 0 and (r['original_name'] == r['returned_name']))
        _require(r['send_code'] == r['invalid_right_constant'] == 268435466)
        _require(r['first_disposition'] == (17 if move else 19) and r['second_disposition'] == 17 and (r['remote_type'] == 19))
        _require(r['second_name'] > 0)
        _require([r[k] for k in ['before_original', 'before_returned', 'after_original', 'after_returned']] == ([0, 0, 0, 0] if move else [1, 1, 1, 1]))
        _require(r['before_endpoint'] == r['after_endpoint'] == 1)
        _require(r['invalid_type_before'] == r['invalid_type_after'] == 131072 and r['invalid_query_after'] == 0)
        _require(r['empty_receive_code'] == 268451843 and r['remaining_send_refs'] == 0 and (r['explicit_cleanup'] is True))
        _require(r['stride'] == 128 and r['allocation_bytes'] == 16384)
        for name in ['before.bin', 'after-error.bin', 'alias-after-cleanup.bin']:
            _require((root / name).read_bytes() == expected)
    _require(len(set(pids)) == 2)
    return {'owned_task_controls': 2, 'full_bytes_compared': 98304, 'padding_bytes': 3240, 'unused_tail_bytes': 91392, 'partial_descriptor_failure_qualified': True, 'moved_first_right_restored': False, 'kernel_internal_copyin_order_traced': False, 'physical_reclamation_qualified': False, 'native_canvas_protocol_qualified': False}
