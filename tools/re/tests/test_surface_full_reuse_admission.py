"""Reject non-native identity/status types, including optimized execution."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from verify_surface_full_reuse import verify
ROOT = Path(__file__).resolve().parents[3]

class TypedReuseEvidenceTests(unittest.TestCase):
    def test_resealed_numeric_type_faults(self):
        for fault in ['float_ids', 'float_pids', 'false_wait']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                e = Path(tmp)/'e'
                shutil.copytree(ROOT/'research/evidence/surface-full-reuse-2026-10-11', e)
                p = e/'wait.json'; wait = json.loads(p.read_text())
                rows = [json.loads(line) for line in wait['stdout'].splitlines()]
                if fault == 'false_wait': wait['code'] = False
                for row, mode in zip(rows, ['reuse', 'separate']):
                    q = e/mode/'receiver.json'; peer = json.loads(q.read_text())
                    for obj in [row, peer]:
                        keys = ['first_id','second_id','live_global_first','live_global_second','final_global_first','final_global_second','first_lookup_after_release','remaining_lookup'] if fault == 'float_ids' else ['sender_pid','receiver_pid'] if fault == 'float_pids' else []
                        for key in keys:
                            if key in obj and obj[key] != 0: obj[key] = float(obj[key])
                    q.write_text(json.dumps(peer))
                wait['stdout'] = ''.join(json.dumps(row)+'\n' for row in rows)
                p.write_text(json.dumps(wait))
                (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q.name!='manifest.json'}}))
                with self.assertRaises(AssertionError): verify(e)

class OptimizedReuseEvidenceTests(unittest.TestCase):
    def test_positive_old_faults_and_typed_faults_under_optimization(self):
        script = """
import sys, unittest
sys.path.insert(0, sys.argv[1])
suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromName('test_surface_full_reuse'),unittest.defaultTestLoader.loadTestsFromName('test_surface_full_reuse_admission.TypedReuseEvidenceTests')])
result=unittest.TextTestRunner().run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
"""
        result = subprocess.run([sys.executable,'-O','-c',script,str(ROOT/'tools/re/tests')], capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
