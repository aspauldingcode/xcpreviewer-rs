"""Complete actual persistent-host corpus plus fixture corruption gating."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from reloop.primarysource import expected

ROOT = Path(__file__).resolve().parents[3]
INPUT = ROOT / 'research/evidence/live-wasm-corpus-2026-10-10/inputs'
RUNNER = ROOT / 'tools/re/reloop/live_wasm_corpus.js'


class LiveCorpusTests(unittest.TestCase):
    def setUp(self):
        self.node = shutil.which('node')
        if not self.node:
            self.skipTest('Node unavailable')

    def test_full_native_and_independent_allocations(self):
        with tempfile.TemporaryDirectory() as temporary:
            subprocess.run([self.node, str(RUNNER), str(INPUT), temporary],
                           check=True, capture_output=True, timeout=45)
            index = json.loads((INPUT / 'corpus.json').read_text())
            result = json.loads((Path(temporary) / 'result.json').read_text())
            self.assertEqual(len(result['records']), 84)
            self.assertEqual(sum(r['native_bytes'] for r in result['records']), 1310720)
            for n, row in enumerate(index['records']):
                raw = (Path(temporary) / ('revision-%d.raw' % n)).read_bytes()
                self.assertEqual(raw, expected(row['config'], row['stride']))
                if row['native']:
                    self.assertEqual(raw, (INPUT / row['native']).read_bytes())
            self.assertEqual(result['final_status']['liveWorkers'], 0)

    def test_changed_module_fails_before_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            shutil.copytree(INPUT, base / 'inputs')
            index = json.loads((base / 'inputs/corpus.json').read_text())
            file = base / 'inputs' / index['records'][0]['module']
            raw = bytearray(file.read_bytes()); raw[-1] ^= 1; file.write_bytes(raw)
            result = subprocess.run([self.node, str(RUNNER), str(base / 'inputs'), str(base / 'outputs')],
                                    capture_output=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(list((base / 'outputs').glob('revision-*.raw')))
