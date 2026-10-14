import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_cli_phase_pair import verify

ROOT = Path(__file__).resolve().parents[3]
FIRST = ROOT/'research/evidence/cli-phase-build-2026-10-14'
SECOND = ROOT/'research/evidence/cli-phase-optimized-2026-10-14'


class CliPhaseTests(unittest.TestCase):
    def test_pair(self):
        self.assertEqual(hashlib.sha256((FIRST/'manifest.json').read_bytes()).hexdigest(),'405d1222de1b7668d3f451bee2098b8b8d8e65bfb171f3543fb1f6ee4ae312a8')
        self.assertEqual(hashlib.sha256((SECOND/'manifest.json').read_bytes()).hexdigest(),'1b4a2a4b5ba6a218042bc95082780b68bc7798c5ad23af3b2ebdf30f0035b4cf')
        self.assertFalse(verify(FIRST,SECOND)['historical_deadline_cause_qualified'])

    def test_resealed_faults(self):
        for fault in ['phase','order','time','identity','erased-failure','budget','padding','module']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                first,second = Path(temporary)/'first',Path(temporary)/'second'
                shutil.copytree(FIRST,first);shutil.copytree(SECOND,second)
                stage = next((first/'builds').glob('build-*'))
                if fault in ['phase','order','time','identity']:
                    path = stage/'cli-phases.jsonl';rows = [json.loads(line) for line in path.read_text().splitlines()]
                    if fault == 'phase': rows[-1]['phase'] = 'postbuild_identity_validated'
                    elif fault == 'order': rows.reverse()
                    elif fault == 'time': rows[-1]['elapsed_seconds'] = -1.0
                    else: rows[0]['cli_sha256'] = '0'*64
                    path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
                elif fault == 'erased-failure':
                    path = first/'outer-wait.json';path.write_text(json.dumps({'code':0,'timeout':False}))
                elif fault == 'budget':
                    path = second/'budget.json';data = json.loads(path.read_text());data['shared_limit'] = 3;path.write_text(json.dumps(data))
                else:
                    path = second/'0-frame.raw' if fault == 'padding' else stage/'result/view.wasm'
                    data = bytearray(path.read_bytes());data[52 if fault == 'padding' else 8] ^= 1;path.write_bytes(data)
                for evidence in [first,second]:
                    files = {str(item.relative_to(evidence)):{'bytes':item.stat().st_size,'sha256':hashlib.sha256(item.read_bytes()).hexdigest()} for item in evidence.rglob('*') if item.is_file() and item.name != 'manifest.json'}
                    (evidence/'manifest.json').write_text(json.dumps({'files':files}))
                with self.assertRaises(AssertionError): verify(first,second)
