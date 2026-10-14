import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_completion_guard import verify

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT/'research/evidence/completion-guard-corrected-2026-10-14'


class CompletionGuardTests(unittest.TestCase):
    def test_pair(self):
        self.assertEqual(hashlib.sha256((EVIDENCE/'manifest.json').read_bytes()).hexdigest(),'1d51e5d0157a2159b9b9fdc35d707046173ac00751e4c738dbde82d10bdf5299')
        self.assertTrue(verify(EVIDENCE)['completion_guard_verified'])

    def test_resealed_faults(self):
        for fault in ['verdict','wait','payload','stdout','terminal-time','delay','sequence','deadline']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                evidence = Path(temporary)/'evidence';shutil.copytree(EVIDENCE,evidence)
                root = evidence/'delayed-zero'
                if fault in ['verdict','wait','stdout']:
                    path = root/'result.json';data = json.loads(path.read_text())
                    if fault == 'verdict': data['record']['report']['failure'] = 'deadline'
                    elif fault == 'wait': data['record']['report']['target_code'] = -15
                    else: data['record']['stdoutSha256'] = '0'*64
                    path.write_text(json.dumps(data))
                elif fault == 'payload':
                    path = root/'owned.raw';path.write_bytes(b'wrong')
                else:
                    path = root/'deadline-audit.jsonl';rows = [json.loads(line) for line in path.read_text().splitlines()]
                    if fault == 'terminal-time': next(row for row in rows if row['kind'] == 'target_poll' and row['code'] is not None)['value'] = 100.0
                    elif fault == 'delay': rows = [row for row in rows if row['kind'] != 'injected_delay_start']
                    elif fault == 'sequence': rows[1]['sequence'] = 1
                    else: rows[0]['milliseconds'] = 5000
                    path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
                files = {str(item.relative_to(evidence)):{'bytes':item.stat().st_size,'sha256':hashlib.sha256(item.read_bytes()).hexdigest()} for item in evidence.rglob('*') if item.is_file() and item.name != 'manifest.json'}
                (evidence/'manifest.json').write_text(json.dumps({'files':files}))
                with self.assertRaises(AssertionError): verify(evidence)
