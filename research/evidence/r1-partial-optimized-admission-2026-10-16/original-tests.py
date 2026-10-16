import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_surface_partial_right import verify

ROOT = Path(__file__).resolve().parents[3]
E = ROOT/'research/evidence/surface-partial-cleanup-2026-10-14'


class SurfacePartialRightTests(unittest.TestCase):
    def test_native_invalid_destination(self):
        self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),'d8c5acef6c6154e836c639869591d0e18d226576cc7bcbf9b9cf6ce6488f1d76')
        self.assertTrue(verify(E)['partial_descriptor_failure_qualified'])
        self.assertEqual((E/'surface_partial_right.c').read_bytes(),(ROOT/'tools/re/surface_partial_right.c').read_bytes())

    def test_resealed_faults(self):
        faults = {'send_code':0,'first_disposition':19,'second_disposition':19,'remote_type':17,'before_original':1,'before_returned':1,'after_returned':1,'invalid_type_after':0,'remaining_send_refs':1,'explicit_cleanup':False,'padding':None,'tail':None}
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
