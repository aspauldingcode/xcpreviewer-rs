import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_surface_send_timeout import verify

ROOT = Path(__file__).resolve().parents[3]
E = ROOT/'research/evidence/surface-send-returned-2026-10-14'


class SurfaceSendTimeoutTests(unittest.TestCase):
    def test_native_measurements(self):
        self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),'385cb1f21b9fbef2c4f11b827349f0144b2fc9baba7b3981dc4d78122d71404d')
        self.assertTrue(verify(E)['returned_rights_accounted'])
        self.assertEqual((E/'surface_send_timeout.c').read_bytes(),(ROOT/'tools/re/surface_send_timeout.c').read_bytes())

    def test_resealed_faults(self):
        for fault in ['name','refs','queue','timeout','disposition','padding','tail','alias']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                e = Path(temporary)/'e';shutil.copytree(E,e)
                p = e/'move/stdout.jsonl';rows = [json.loads(line) for line in p.read_text().splitlines()]
                if fault == 'name': rows[0]['returned_name'] = rows[0]['original_name']
                elif fault == 'refs': rows[0]['returned_refs'] = 0
                elif fault == 'queue': rows[1]['queue_count'] = 2
                elif fault == 'timeout': rows[1]['send_code'] = 0
                elif fault == 'disposition': rows[1]['returned_disposition'] = 19
                elif fault == 'alias': rows[1]['alias_survives'] = False
                else:
                    p = e/'move/alias-after-right-release.bin';raw = bytearray(p.read_bytes());raw[68 if fault == 'padding' else 16383] ^= 1;p.write_bytes(raw);rows = None
                if rows is not None: p.write_text(''.join(json.dumps(row)+'\n' for row in rows))
                (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name != 'manifest.json'}}))
                with self.assertRaises(AssertionError): verify(e)
