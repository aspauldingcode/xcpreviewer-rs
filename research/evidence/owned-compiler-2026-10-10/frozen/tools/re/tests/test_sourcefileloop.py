"""Actual owned file polling and cooperative builder closure controls."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]

class SourceFileLoopTests(unittest.TestCase):
    def test_actual_file_edits_and_close(self):
        node=shutil.which('node')
        if not node:self.skipTest('Existing Node required')
        with tempfile.TemporaryDirectory() as out:
            subprocess.run([node,str(ROOT/'tools/re/tests/source_file_loop_control.js'),
                            str(ROOT/'research/evidence/source-revision-2026-10-10'),out],
                           check=True,timeout=15,capture_output=True)
            result=json.loads((Path(out)/'file-loop-result.json').read_text())
            self.assertEqual(result['accepted'],3)
            self.assertEqual(len(result['controls']),7)
            self.assertEqual(result['aborts'],1)
            self.assertEqual(result['deadlineAborts'],1)
            self.assertEqual(result['final_status']['liveWorkers'],0)
