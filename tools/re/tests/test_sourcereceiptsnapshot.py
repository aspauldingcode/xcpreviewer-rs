"""Actual V8 source/module receipt snapshot controls, independent frozen frames."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]
class SourceReceiptSnapshotTests(unittest.TestCase):
    def test_getters_and_source_overrides_cannot_change_snapshot_identity(self):
        node = shutil.which('node')
        if not node: self.skipTest('Existing Node required')
        with tempfile.TemporaryDirectory() as out:
            subprocess.run([node, str(ROOT/'tools/re/tests/source_receipt_snapshot_control.js'),
                            str(ROOT/'tools/re/reloop/source_revision_host.js'), out],
                           check=True, capture_output=True, timeout=15)
            result = json.loads((Path(out)/'result.json').read_text())
            self.assertEqual(result['failures'], 0)
            self.assertEqual(len(result['results']), 5)
            self.assertEqual(result['final_owned_workers'], 0)
            self.assertTrue(all(row['passed'] for row in result['results']))
