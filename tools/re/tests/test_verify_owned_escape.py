import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('escape_verifier', Path(__file__).with_name('verify_owned_escape.py'))
verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)


class EscapeReceiptTests(unittest.TestCase):
    def test_actual_sealed_controls(self):
        result = verifier.verify(ROOT/'research/evidence/owned-escape-2026-10-10')
        self.assertEqual(result['controls'], 4)
        self.assertEqual(result['scientific_delivery_review'], 'pending')

    def test_corruption_and_resealed_false_claims_rejected(self):
        mutations = [lambda d:d['controls'][2].update(late_write=True),
                     lambda d:d['controls'][0].update(parent_after=d['controls'][0]['parent_before']),
                     lambda d:d['controls'][3]['target_status']['record'].update(code=0),
                     lambda d:d['identity_mutants'][1].update(no_signal=False)]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)/'evidence'
                shutil.copytree(ROOT/'research/evidence/owned-escape-2026-10-10', folder)
                path = folder/'control/result.json'; data = json.loads(path.read_text())
                mutation(data); path.write_text(json.dumps(data))
                # Reseal altered bytes: independent semantic gate must still fail.
                manifest = json.loads((folder/'manifest.json').read_text())
                manifest['files']['control/result.json'] = {'bytes':path.stat().st_size,
                    'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
                (folder/'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(AssertionError): verifier.verify(folder)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)/'evidence'
            shutil.copytree(ROOT/'research/evidence/owned-escape-2026-10-10', folder)
            (folder/'control/result.json').write_bytes(b'corrupt')
            with self.assertRaises(AssertionError): verifier.verify(folder)
