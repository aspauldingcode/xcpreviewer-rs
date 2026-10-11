"""Actual FIFO/path-replacement controls under an external owned deadline."""
import json
import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('input_verifier',Path(__file__).with_name('verify_source_input.py'))
verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)


class SourceInputGateTests(unittest.TestCase):
    def test_owned_nonregular_and_replaced_inputs(self):
        node=shutil.which('node')
        if not node:self.skipTest('Existing Node required')
        with tempfile.TemporaryDirectory() as out:
            p=subprocess.run([node,str(ROOT/'tools/re/tests/source_input_control.js'),out,
                              str(ROOT/'tools/re/reloop/source_file_loop.js')],
                             capture_output=True,timeout=5)
            self.assertEqual(p.returncode,0,p.stderr.decode())
            result=json.loads((Path(out)/'result.json').read_text())
            self.assertEqual(len(result['controls']),7)
            self.assertEqual(sum(r['builds'] for r in result['controls']),1)

    def test_sealed_input_controls(self):
        self.assertEqual(verifier.verify(ROOT/'research/evidence/source-input-gate-2026-10-10')['controls'],7)

    def test_resealed_false_claims_rejected(self):
        mutations=[lambda d:d['controls'][5].update(closed=0),
                   lambda d:d['controls'][0].update(deadlineAutoClosed=False),
                   lambda d:d['controls'][6].update(builds=1),
                   lambda d:d['controls'][0]['status'].update(timers=1)]
        for mutation in mutations:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as out:
                folder=Path(out)/'evidence'
                shutil.copytree(ROOT/'research/evidence/source-input-gate-2026-10-10',folder)
                p=folder/'after/result.json';d=json.loads(p.read_text());mutation(d);p.write_text(json.dumps(d))
                manifest=json.loads((folder/'manifest.json').read_text())
                manifest['files']['after/result.json']={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                (folder/'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(AssertionError):verifier.verify(folder)
