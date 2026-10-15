import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_surface_send_retry import verify

ROOT = Path(__file__).resolve().parents[3]
E = ROOT/'research/evidence/surface-send-retry-2026-10-14'


class SurfaceSendRetryTests(unittest.TestCase):
    def test_native_retry(self):
        self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),'dd67a2fa3a3f083e487f8bec30dafe634551bc4268ffb3d11e416e67151c47d6')
        self.assertTrue(verify(E)['returned_envelope_retry_qualified'])
        self.assertEqual((E/'surface_send_retry.c').read_bytes(),(ROOT/'tools/re/surface_send_retry.c').read_bytes())

    def test_resealed_faults(self):
        faults = {'retry_code':1,'timeout_code':0,'returned_remote_type':19,'before_returned':0,'after_send_returned':1,'after_receive_imported':0,'after_destroy_imported':1,'remaining_send_refs':1,'same_surface_id':False,'surface_id':0,'padding':None,'tail':None}
        for fault, value in faults.items():
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                e = Path(temporary)/'e';shutil.copytree(E,e)
                p = e/'move/stdout.jsonl';r = json.loads(p.read_text())
                if fault in ['padding','tail']:
                    p = e/'move/import-after-cleanup.bin';raw = bytearray(p.read_bytes());raw[68 if fault == 'padding' else 16383] ^= 1;p.write_bytes(raw)
                else:
                    r[fault] = value;p.write_text(json.dumps(r)+'\n')
                (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name != 'manifest.json'}}))
                with self.assertRaises(AssertionError): verify(e)
