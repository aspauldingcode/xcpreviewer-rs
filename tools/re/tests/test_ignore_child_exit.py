import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_ignore_child_exit import verify

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT/'research/evidence/ignore-child-exit-2026-10-14'


class IgnoreChildTests(unittest.TestCase):
    def test_measurements(self):
        self.assertEqual(verify(EVIDENCE)['child_signals'],[9,9])
        self.assertEqual((ROOT/'tools/re/tests/ignore_child_exit_control.js').read_bytes(),(EVIDENCE/'control.js').read_bytes())

    def test_resealed_faults(self):
        for name in ['signal','birth','receipt','prediction','wait','disposition']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                evidence = Path(temporary)/'evidence'
                shutil.copytree(EVIDENCE,evidence)
                if name == 'disposition':
                    path = evidence/'target.py'
                    path.write_text(path.read_text().replace('signal.SIG_IGN','signal.SIG_DFL'))
                else:
                    target = {'signal':'running-0/kernel-exit-events.json','birth':'running-0/registered.json','receipt':'running-0/result.json','prediction':'prediction.json','wait':'wait-running-0.json'}[name]
                    path = evidence/target
                    data = json.loads(path.read_text())
                    if name == 'signal': data[1]['data'] = 15
                    elif name == 'birth': data['birth_rechecked'] = False
                    elif name == 'receipt': data['record']['report']['drained'] = False
                    elif name == 'prediction': data['child_raw_status'] = 15
                    else: data['code'] = 1
                    path.write_text(json.dumps(data))
                files = {str(path.relative_to(evidence)):{'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in evidence.rglob('*') if path.is_file() and path.name != 'manifest.json'}
                (evidence/'manifest.json').write_text(json.dumps({'files':files}))
                with self.assertRaises(AssertionError): verify(evidence)
