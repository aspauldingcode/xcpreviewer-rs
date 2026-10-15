import hashlib
import json
from pathlib import Path
from reloop.primarysource import parse, expected


def verify(folder):
    e = Path(folder);manifest = json.loads((e/'manifest.json').read_text())
    assert set(manifest['files']) == {str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    for name, item in manifest['files'].items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        p = e/name;raw = p.read_bytes()
        assert not p.is_symlink() and len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
    assert json.loads((e/'slots.json').read_text()) == {'used':2,'limit':2}
    rea = json.loads((e/'current-rea.json').read_text())
    assert rea['target']['sha256'] == '768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e' and rea['target']['architecture'] == 'arm64'
    assert rea['server']['version'] == '6.2.0'
    full = (e/'fixture/0-source.swift').read_bytes()
    assert len(full) == 202 and hashlib.sha256(full).hexdigest() == '37c2bf5abe8c1124cd2e57d8fe3de47964e626398faab3029a41d097bebc77a8'
    oracle = expected(parse(full.decode()),64)
    assert len(oracle) == 16384 and (e/'fixture/0-expected.raw').read_bytes() == oracle
    assert hashlib.sha256((e/'fixture/0-view.wasm').read_bytes()).hexdigest() == '4dacf7c144daef769fa079f02bdcf9e003187aa3e9d1e08efbb834043a5ccd6e'
    pins = {'before':'60a2b520b134fcae5df090910fc0e271108a28ce311bed9904f9f4ad233337bb','after':'0747cd8c9fa9f7437e4533099cc18124cbdb4e5386d243a1dbf0b5529fd1f201'}
    for mode in ['before','after']:
        root = e/mode
        assert hashlib.sha256((root/'source_file_loop.js').read_bytes()).hexdigest() == pins[mode]
        assert json.loads((root/'wait.json').read_text()) == {'code':0,'timeout':False,'stdout':'','stderr':''}
        data = json.loads((root/'result.json').read_text());assert data['mode'] == mode
        assert [c['kind'] for c in data['cases']] == ['valid','oversize','empty']
        for case, source in zip(data['cases'],[full,b'A'*4097,b'']):
            kind = case['kind'];sha = hashlib.sha256
            assert (root/kind/'owned.swift').read_bytes() == source
            assert case['sourceBytes'] == len(source) and case['sourceSha256'] == sha(source).hexdigest()
            assert case['opens'] == case['closes'] == 1
            reads=[];used=0
            while used < 4097:
                n=min(7,len(source)-used,4097-used)
                reads.append({'offset':used,'requested':4097-used,'position':used,'count':n,'hex':source[used:used+n].hex()})
                used+=n
                if n==0 or mode=='before':break
            assert case['reads'] == reads
            valid = mode == 'after' and kind == 'valid'
            assert case['published'] is valid
            built = source if valid else source[:7] if mode=='before' and kind!='empty' else None
            assert case['builds'] == ([] if built is None else [{'bytes':len(built),'sha256':sha(built).hexdigest()}])
            events = case['events']
            if valid:
                assert [r['kind'] for r in events] == ['observed','published'] and events[1]['revision'] == 1
                assert events[0]['sourceSha256'] == events[1]['sourceSha256'] == sha(source).hexdigest()
                assert (root/kind/'accepted.raw').read_bytes() == oracle
            elif built is not None:
                assert [r['kind'] for r in events] == ['observed','rejected']
                assert events[0]['sourceSha256'] == sha(built).hexdigest() and 'Owned adapter requires complete source' in events[1]['error']
                assert not (root/kind/'accepted.raw').exists()
            else:
                assert events == [{'kind':'invalid-source'}] and not (root/kind/'accepted.raw').exists()
            assert case['status'] == {'liveWorkers':0,'busy':False,'closed':True,'revision':1 if valid else 0,'loopClosed':True,'building':False,'timers':0}
    return {'real_file_cases':6,'read_chunk_cap':7,'source_byte_cap':4097,'full_allocation_bytes':16384,'padding_bytes':84,'unused_tail_bytes':15936,'source_short_read_fix_qualified':True,'fresh_compiler_builds':0,'natural_short_reads_observed':False,'native_canvas_protocol_qualified':False}
