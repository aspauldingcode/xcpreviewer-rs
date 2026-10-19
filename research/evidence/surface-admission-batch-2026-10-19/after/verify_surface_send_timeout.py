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
    _require(identity['sha256'] == rea['target']['sha256'] == 'db0f71dcdc7ac54b2cbc2cf38276aa9dba4fb1283db55f3c96c805d80b767018')
    _require(rea['target']['architecture'] == 'arm64' and rea['server']['version'] == '6.2.0')
    _require(identity['owned_case_limit'] == 2 and identity['private_capture_bridge_available'] is False)
    expected = bytearray([165] * 16384)
    for y in range(9):
        for x in range(17):
            for c in range(4):
                expected[y * 128 + x * 4 + c] = 255 if c == 3 else 49 + x * 17 + y * 31 + c * 53 & 255
    outcomes = []
    for mode in ['copy', 'move']:
        root = e / mode
        move = mode == 'move'
        _require(json.loads((root / 'wait.json').read_text()) == {'code': 0, 'timeout': False})
        _require((root / 'stderr').read_bytes() == b'')
        rows = [json.loads(line) for line in (root / 'stdout.jsonl').read_text().splitlines()]
        _require(len(rows) == 2)
        (names, result) = rows
        _require(type(names['original_name']) is int and names['original_name'] > 0)
        _require(type(names['returned_name']) is int and names['returned_name'] > 0)
        _require((names['original_name'] == names['returned_name']) == names['names_equal'] == (not move))
        _require(names['returned_refs'] == (1 if move else 2) and names['returned_name_removed'] is True)
        _require(result['move'] is move and result['pid'] > 0)
        _require(result['send_code'] == result['timeout_constant'] == 268435460)
        _require(result['empty_receive_code'] == result['empty_receive_constant'] == 268451843)
        _require(result['resource_refs_after_failure'] == (0 if move else 2))
        _require(result['endpoint_refs_after_failure'] == 2 and result['returned_disposition'] == 17)
        _require(result['queue_count'] == result['queue_limit'] == 1)
        _require(result['resource_name_removed'] is result['endpoint_removed'] is result['alias_survives'] is True)
        _require([result[k] for k in ['width', 'height', 'seed', 'stride', 'allocation_bytes']] == [17, 9, 49, 128, 16384])
        for name in ['before.bin', 'after-timeout.bin', 'alias-after-right-release.bin']:
            _require((root / name).read_bytes() == expected)
        outcomes.append({'mode': mode, 'original_refs': result['resource_refs_after_failure'], 'returned_refs': names['returned_refs'], 'name_changed': move})
    return {'owned_task_controls': 2, 'full_bytes_compared': 98304, 'padding_bytes': 3240, 'unused_tail_bytes': 91392, 'outcomes': outcomes, 'returned_rights_accounted': True, 'physical_reclamation_qualified': False, 'native_canvas_protocol_qualified': False}
