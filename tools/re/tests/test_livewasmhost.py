"""Actual bounded V8 instance/frame swap and trap/timeout controls."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


class LiveWasmHostTests(unittest.TestCase):
    def test_actual_worker_instances_and_failed_proposals(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node unavailable')
        evidence = ROOT / 'research/evidence/live-wasm-swap-2026-10-10'
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            for name in ('fixtures.json', '0-view.wasm', '1-view.wasm',
                         '0-allocation.raw', '1-allocation.raw'):
                shutil.copyfile(evidence / name, target / name)
            subprocess.run([node, str(ROOT / 'tools/re/tests/live_wasm_host_control.js'), str(target)],
                           check=True, timeout=15, capture_output=True)
            result = json.loads((target / 'control-result.json').read_text())
            self.assertEqual(result['accepted'], 2)
            self.assertEqual(len(result['faults']), 6)
            self.assertTrue(all(row['live_instance_verified'] for row in result['faults']))
