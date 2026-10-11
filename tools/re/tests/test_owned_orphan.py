"""Actual target exit with an inherited child holding stdout."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[3]

class OwnedOrphanTests(unittest.TestCase):
    def test_success_and_failure_exit_drain_inherited_child(self):
        node=shutil.which('node')
        if not node:self.skipTest('Existing Node required')
        with tempfile.TemporaryDirectory() as out:
            subprocess.run([node,str(ROOT/'tools/re/tests/owned_orphan_control.js'),out,
                            str(ROOT/'tools/re/reloop/owned_compiler.js'),sys.executable,'verify'],
                           check=True,timeout=10,capture_output=True)
            result=json.loads((Path(out)/'orphan-result.json').read_text())
            self.assertEqual(result['failures'],0)
            self.assertEqual([c['code'] for c in result['controls']],[0,7])
