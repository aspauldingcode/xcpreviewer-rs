import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_phase_deadline_boundary import verify

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT/'research/evidence/builder-phase-recovery-2026-10-14'


class PhaseDeadlineTests(unittest.TestCase):
    def test_boundary(self):
        self.assertEqual(hashlib.sha256((EVIDENCE/'manifest.json').read_bytes()).hexdigest(),'c27420b678797874359771e51d550a2e25bfcca645fc25f380bdc087df2d50b4')
        self.assertFalse(verify(EVIDENCE)['completion_before_deadline_qualified'])

    def test_resealed_faults(self):
        for fault in ['verdict','wait','receipt','stdout','phase','module','closure','outer']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                evidence = Path(temporary)/'evidence';shutil.copytree(EVIDENCE,evidence)
                path = evidence/'retained-failure.json';data = json.loads(path.read_text())
                if fault == 'verdict': data['failures'][0]['record']['report']['failure'] = None
                elif fault == 'wait': data['failures'][0]['record']['report']['target_code'] = -15
                elif fault == 'receipt': data['failures'][0]['record']['stdout'] = '{}'
                elif fault == 'stdout': data['failures'][0]['record']['stdoutSha256'] = '0'*64
                elif fault == 'phase':
                    path = next((evidence/'builds').glob('build-*'))/'cli-phases.jsonl';path.write_text('\n'.join(path.read_text().splitlines()[:-1])+'\n');data = None
                elif fault == 'module':
                    path = next((evidence/'builds').glob('build-*'))/'result/view.wasm';payload = bytearray(path.read_bytes());payload[8] ^= 1;path.write_bytes(payload);data = None
                elif fault == 'closure':
                    path = evidence/'closure.json';data = json.loads(path.read_text());data['revision'] = 1
                else:
                    path = evidence/'outer-wait.json';data = json.loads(path.read_text());data['code'] = 0
                if data is not None: path.write_text(json.dumps(data))
                files = {str(item.relative_to(evidence)):{'bytes':item.stat().st_size,'sha256':hashlib.sha256(item.read_bytes()).hexdigest()} for item in evidence.rglob('*') if item.is_file() and item.name != 'manifest.json'}
                (evidence/'manifest.json').write_text(json.dumps({'files':files}))
                with self.assertRaises(AssertionError): verify(evidence)
