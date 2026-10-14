import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_builder_kernel_failure import verify

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT/'research/evidence/builder-kernel-cancel-2026-10-14'


class BuilderKernelFailureTests(unittest.TestCase):
    def test_partial_measurements(self):
        self.assertEqual(hashlib.sha256((EVIDENCE/'manifest.json').read_bytes()).hexdigest(),'f531ba17e0232a64f1016dae2aab82c183122994e5b7f2fe055605ac625bc946')
        self.assertFalse(verify(EVIDENCE)['recovery_qualified'])
        self.assertEqual((EVIDENCE/'control.js').read_bytes(),(ROOT/'tools/re/tests/builder_kernel_cancel_control.js').read_bytes())

    def test_resealed_faults(self):
        for fault in ['erased-failure','deadline','kernel','registration','watcher','closure','padding','outer']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                evidence = Path(temporary)/'evidence'
                shutil.copytree(EVIDENCE,evidence)
                path = evidence/'retained-failure.json'
                data = json.loads(path.read_text())
                if fault == 'erased-failure': data['qualified'] = True
                elif fault == 'deadline': data['failures'][1]['record']['report']['failure'] = None
                elif fault == 'registration': data['trigger']['registration']['micros'] = -1
                elif fault in ['kernel','watcher']:
                    path = evidence/'compiler-kernel-wait.json'
                    data = json.loads(path.read_text())
                    if fault == 'watcher': data['code'] = 1
                    else: data['stdout'] = data['stdout'].replace('"raw_status":15','"raw_status":9')
                elif fault == 'closure':
                    path = evidence/'closure.json'
                    data = json.loads(path.read_text());data['liveWorkers'] = 1
                elif fault == 'outer':
                    path = evidence/'outer-wait.json'
                    data = json.loads(path.read_text());data['code'] = 0
                else:
                    path = evidence/'retained-at-cancel.raw'
                    payload = bytearray(path.read_bytes());payload[52] ^= 1;path.write_bytes(payload);data = None
                if data is not None: path.write_text(json.dumps(data))
                files = {str(item.relative_to(evidence)):{'bytes':item.stat().st_size,'sha256':hashlib.sha256(item.read_bytes()).hexdigest()} for item in evidence.rglob('*') if item.is_file() and item.name != 'manifest.json'}
                (evidence/'manifest.json').write_text(json.dumps({'files':files}))
                with self.assertRaises(AssertionError): verify(evidence)
