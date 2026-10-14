import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_snapshot_timing import verify

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT/'research/evidence/toolchain-snapshot-timing-2026-10-14'


class SnapshotTimingTests(unittest.TestCase):
    def test_measurements(self):
        self.assertEqual(hashlib.sha256((EVIDENCE/'manifest.json').read_bytes()).hexdigest(),'666005d77ad22e8d22ccbc00453867cf7adfa31a4eb24550499914dfe93b90d9')
        self.assertFalse(verify(EVIDENCE)['historical_deadline_cause_qualified'])
        self.assertEqual((EVIDENCE/'control.py').read_bytes(),(ROOT/'tools/re/tests/toolchain_snapshot_timing.py').read_bytes())

    def test_resealed_faults(self):
        for fault in ['duration','pin','query-wait','stdout','file','scope','rea','outer']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                evidence = Path(temporary)/'evidence'
                shutil.copytree(EVIDENCE,evidence)
                path = evidence/'snapshot-0.json';data = json.loads(path.read_text())
                if fault == 'duration': data['elapsed_seconds'] = 6.0
                elif fault == 'pin': data['identity']['compiler_file']['sha256'] = '0'*64
                elif fault == 'query-wait': data['queries'][0]['wait_code'] = 1
                elif fault == 'stdout': data['queries'][0]['stdout_sha256'] = '0'*64
                elif fault == 'file': data['files'][0]['identity']['bytes'] += 1
                elif fault == 'scope':
                    path = evidence/'prediction.json';data = json.loads(path.read_text());data['historical_deadline_cause_qualified'] = True
                elif fault == 'rea':
                    path = evidence/'rea-status.json';data = json.loads(path.read_text());data['target']['sha256'] = '0'*64
                else:
                    path = evidence/'outer-wait.json';data = json.loads(path.read_text());data['code'] = 1
                path.write_text(json.dumps(data))
                files = {str(item.relative_to(evidence)):{'bytes':item.stat().st_size,'sha256':hashlib.sha256(item.read_bytes()).hexdigest()} for item in evidence.rglob('*') if item.is_file() and item.name != 'manifest.json'}
                (evidence/'manifest.json').write_text(json.dumps({'files':files}))
                with self.assertRaises(AssertionError): verify(evidence)
