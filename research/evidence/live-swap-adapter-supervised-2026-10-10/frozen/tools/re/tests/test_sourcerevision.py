import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


class SourceRevisionTests(unittest.TestCase):
    def test_stale_builds_and_atomic_source_provenance(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node unavailable')
        with tempfile.TemporaryDirectory() as out:
            subprocess.run([node, str(ROOT / 'tools/re/tests/source_revision_control.js'),
                            str(ROOT / 'research/evidence/source-revision-2026-10-10'), out],
                           capture_output=True, check=True, timeout=15)
            result = json.loads((Path(out) / 'source-result.json').read_text())
            self.assertEqual(result['accepted_revisions'], 3)
            self.assertEqual(result['source_generations'], 6)
            self.assertEqual(len(result['controls']), 5)
            self.assertEqual(result['final_status']['liveWorkers'], 0)
