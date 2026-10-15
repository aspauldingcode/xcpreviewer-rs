import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_surface_send_destroy import verify

ROOT = Path(__file__).resolve().parents[3]
E = ROOT/'research/evidence/surface-send-destroy-2026-10-14'


class SurfaceSendDestroyTests(unittest.TestCase):
    def test_native_measurements(self):
        self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),'bc202e0c981843dd6af7f4c536c5bfc54e1c77c4290526839e9753fdb3699c4c')
        self.assertTrue(verify(E)['returned_rights_accounted'])
        self.assertEqual((E/'surface_send_destroy.c').read_bytes(),(ROOT/'tools/re/surface_send_destroy.c').read_bytes())

    def test_resealed_faults(self):
        for fault in ['name','refs','queue','timeout','disposition','padding','tail','alias','before','destroy']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                e = Path(temporary)/'e';shutil.copytree(E,e)
                p = e/'move/stdout.jsonl';rows = [json.loads(line) for line in p.read_text().splitlines()]
                if fault == 'name': rows[1]['returned_name'] = rows[1]['original_name']
                elif fault == 'refs': rows[1]['returned_refs'] = 1
                elif fault == 'before': rows[0]['returned_before_destroy'] = 0
                elif fault == 'destroy': rows[0]['destroy_called_once'] = False
                elif fault == 'queue': rows[2]['queue_count'] = 2
                elif fault == 'timeout': rows[2]['send_code'] = 0
                elif fault == 'disposition': rows[2]['returned_disposition'] = 19
                elif fault == 'alias': rows[2]['alias_survives'] = False
                else:
                    p = e/'move/alias-after-right-release.bin';raw = bytearray(p.read_bytes());raw[68 if fault == 'padding' else 16383] ^= 1;p.write_bytes(raw);rows = None
                if rows is not None: p.write_text(''.join(json.dumps(row)+'\n' for row in rows))
                (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name != 'manifest.json'}}))
                with self.assertRaises(AssertionError): verify(e)
