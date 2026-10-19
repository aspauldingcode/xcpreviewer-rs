import hashlib
import json
from pathlib import Path


def verify(folder):
    e = Path(folder);manifest = json.loads((e/'manifest.json').read_text())
    assert set(manifest['files']) == {str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    for name, item in manifest['files'].items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        p = e/name;raw = p.read_bytes()
        assert not p.is_symlink() and len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
    assert json.loads((e/'slots.json').read_text()) == {'used':2,'limit':2}
    assert json.loads((e/'compile-wait.json').read_text()) == {'code':0}
    identity = json.loads((e/'identity.json').read_text());rea = json.loads((e/'current-rea.json').read_text())
    assert identity['sha256'] == rea['target']['sha256'] == '408de41cbb83abb164127905a736fa78768763f82a79f76d257ff5ba3e3060f7'
    assert rea['target']['architecture'] == 'arm64' and rea['server']['version'] == '6.2.0'
    assert identity['owned_case_limit'] == 2 and identity['private_capture_bridge_available'] is False
    expected = bytearray([0xa5]*16384)
    for y in range(9):
        for x in range(17):
            for c in range(4): expected[y*128+x*4+c] = 255 if c == 3 else (49+x*17+y*31+c*53)&255
    outcomes = []
    pids = []
    for mode in ['copy','move']:
        root = e/mode;move = mode == 'move'
        assert json.loads((root/'wait.json').read_text()) == {'code':0,'timeout':False}
        assert (root/'stderr').read_bytes() == b''
        rows = [json.loads(line) for line in (root/'stdout.jsonl').read_text().splitlines()]
        assert len(rows) == 1
        r = rows[0];assert r['move'] is move and r['pid'] > 0 and r['surface_id'] > 0
        pids.append(r['pid'])
        names = [r[k] for k in ['original_name','returned_name','received_name']]
        assert all(type(n) is int and n > 0 for n in names)
        assert len(set(names)) == (3 if move else 1)
        assert r['timeout_code'] == 268435460 and r['retry_code'] == 0
        assert r['returned_disposition'] == r['returned_remote_type'] == 17
        assert [r[k] for k in ['before_original','before_returned','before_endpoint']] == ([0,1,2] if move else [2,2,2])
        assert [r[k] for k in ['after_send_original','after_send_returned','after_send_endpoint']] == ([0,0,1] if move else [1,1,1])
        assert [r[k] for k in ['after_receive_original','after_receive_imported']] == ([0,1] if move else [2,2])
        assert [r[k] for k in ['after_destroy_original','after_destroy_imported']] == ([0,0] if move else [1,1])
        assert r['remaining_send_refs'] == 0 and r['endpoint_removed'] is r['same_surface_id'] is True
        assert r['stride'] == 128 and r['allocation_bytes'] == 16384
        for name in ['before.bin','after-timeout.bin','received.bin','import-after-cleanup.bin']:
            assert (root/name).read_bytes() == expected
        outcomes.append({'mode':mode,'retry_code':0,'task_local_names':len(set(names)),'surface_id':r['surface_id']})
    assert len(set(pids)) == 2
    return {'owned_task_controls':2,'full_bytes_compared':131072,'padding_bytes':4320,'unused_tail_bytes':121856,'outcomes':outcomes,'returned_envelope_retry_qualified':True,'cross_task_numeric_id_identity_qualified':False,'physical_reclamation_qualified':False,'native_canvas_protocol_qualified':False}
