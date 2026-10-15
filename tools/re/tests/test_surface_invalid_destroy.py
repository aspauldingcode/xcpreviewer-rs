import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_surface_invalid_destroy import verify

ROOT = Path(__file__).resolve().parents[3]
E = ROOT/'research/evidence/surface-invalid-destroy-2026-10-14'


class SurfaceInvalidDestroyTests(unittest.TestCase):
    def test_native_invalid_destination(self):
        self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),'a18ecb92916246ca58361d2df158cf9bd12fcb24d6621da910765e4d5fb9ef11')
        self.assertTrue(verify(E)['invalid_destination_ownership_qualified'])
        self.assertEqual((E/'surface_invalid_destroy.c').read_bytes(),(ROOT/'tools/re/surface_invalid_destroy.c').read_bytes())

    def test_resealed_faults(self):
        faults = {'send_code':0,'returned_disposition':19,'remote_type':17,'resource_refs_before_destroy':0,'resource_refs_after_destroy':1,'dead_refs_before':0,'dead_refs_after_destroy':0,'returned_name':0,'explicit_remaining_rights_removed':False,'alias_survives':False,'padding':None,'tail':None}
        for fault, value in faults.items():
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                e = Path(temporary)/'e';shutil.copytree(E,e)
                p = e/'move/stdout.jsonl';r = json.loads(p.read_text())
                if fault in ['padding','tail']:
                    p = e/'move/alias-after-cleanup.bin';raw = bytearray(p.read_bytes());raw[68 if fault == 'padding' else 16383] ^= 1;p.write_bytes(raw)
                else:
                    r[fault] = value;p.write_text(json.dumps(r)+'\n')
                (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name != 'manifest.json'}}))
                with self.assertRaises(AssertionError): verify(e)
