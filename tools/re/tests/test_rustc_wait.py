import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_rustc_wait import verify

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT/'research/evidence/rustc-child-wait-2026-10-14'


class RustcWaitTests(unittest.TestCase):
    def test_measurements(self):
        self.assertEqual(hashlib.sha256((EVIDENCE/'manifest.json').read_bytes()).hexdigest(),'0aa66cc68048448ca0bcdecf65b07bf1e3f4c318b0b90052efdcaca2d5ac1d46')
        self.assertEqual(verify(EVIDENCE)['actual_rustc_wait_codes'],[-15,-15,0,0])
        self.assertEqual((EVIDENCE/'control.py').read_bytes(),(ROOT/'tools/re/tests/rustc_wait_control.py').read_bytes())

    def test_resealed_faults(self):
        for fault in ['wait','parent','birth','path','recheck','source','output','scope']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                evidence = Path(temporary)/'evidence'
                shutil.copytree(EVIDENCE,evidence)
                path = evidence/'cancel-0/result.json'
                data = json.loads(path.read_text())
                if fault == 'wait': data['wait_code'] = 0
                elif fault == 'parent': data['observation']['parent'] = 1
                elif fault == 'birth': data['observation']['identity'][1] = -1
                elif fault == 'path': data['observation']['identity'][2] = '/wrong'
                elif fault == 'recheck': data['rechecked'] = []
                elif fault == 'output': data['output_present'] = True
                elif fault == 'scope':
                    path = evidence/'prediction.json'
                    data = json.loads(path.read_text())
                    data['supervisor_integration_qualified'] = True
                else:
                    path = evidence/'cancel-0/input.rs'
                    path.write_bytes(b'wrong')
                    data = None
                if data is not None: path.write_text(json.dumps(data))
                files = {str(item.relative_to(evidence)):{'bytes':item.stat().st_size,'sha256':hashlib.sha256(item.read_bytes()).hexdigest()} for item in evidence.rglob('*') if item.is_file() and item.name != 'manifest.json'}
                (evidence/'manifest.json').write_text(json.dumps({'files':files}))
                with self.assertRaises(AssertionError): verify(evidence)
