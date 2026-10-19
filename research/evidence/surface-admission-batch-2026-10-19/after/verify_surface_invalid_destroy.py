def _require(condition):
    if not condition:
        raise AssertionError('Surface lifecycle evidence rejected')

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
    _require(json.loads((e / 'compile-wait.json').read_text()) == {'code': 0})
    identity = json.loads((e / 'identity.json').read_text())
    rea = json.loads((e / 'current-rea.json').read_text())
    _require(identity['sha256'] == rea['target']['sha256'] == '07dda5f443ba9f812a26db99e8b1ea7843f6c7cc2ed740bea4637a360a456e6e')
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
        _require(json.loads((root / 'wait.json').read_text()) == {'code': 0, 'timeout': False})
        _require((root / 'stderr').read_bytes() == b'')
        rows = [json.loads(line) for line in (root / 'stdout.jsonl').read_text().splitlines()]
        _require(len(rows) == 1)
        r = rows[0]
        _require(r['move'] is move and r['pid'] > 0)
        pids.append(r['pid'])
        _require(type(r['original_name']) is int and r['original_name'] > 0 and (r['original_name'] == r['returned_name']))
        _require(r['send_code'] == r['invalid_dest_constant'] == 268435459)
        _require(r['returned_disposition'] == (17 if move else 19) and r['remote_type'] == 19)
        _require(r['resource_refs_before_destroy'] == 1 and r['resource_refs_after_destroy'] == (0 if move else 1))
        _require(r['dead_refs_before'] == r['dead_refs_after_destroy'] == 1)
        _require(r['explicit_remaining_rights_removed'] is r['alias_survives'] is True)
        _require(r['stride'] == 128 and r['allocation_bytes'] == 16384)
        for name in ['before.bin', 'after-invalid-dest.bin', 'alias-after-cleanup.bin']:
            _require((root / name).read_bytes() == expected)
    _require(len(set(pids)) == 2)
    return {'owned_task_controls': 2, 'full_bytes_compared': 98304, 'padding_bytes': 3240, 'unused_tail_bytes': 91392, 'invalid_destination_ownership_qualified': True, 'kernel_internal_copyin_order_traced': False, 'physical_reclamation_qualified': False, 'native_canvas_protocol_qualified': False}
