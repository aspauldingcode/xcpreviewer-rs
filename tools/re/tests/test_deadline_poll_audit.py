import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from verify_deadline_poll_audit import verify

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT/'research/evidence/deadline-poll-audit-2026-10-14'


class DeadlineAuditTests(unittest.TestCase):
    def test_measurements(self):
        self.assertEqual(hashlib.sha256((EVIDENCE/'manifest.json').read_bytes()).hexdigest(),'ded812fbefea48a7ad2272f18b255aeb5c709f1379557d2011d439c8ae9b8d40')
        self.assertFalse(verify(EVIDENCE)['false_deadline_observed'])
        self.assertEqual((EVIDENCE/'audit.py').read_bytes(),(ROOT/'tools/re/tests/owned_deadline_audit.py').read_bytes())

    def test_resealed_faults(self):
        for fault in ['deadline','poll','sequence','pid','identity','frame','verdict','closure']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                evidence = Path(temporary)/'evidence';shutil.copytree(EVIDENCE,evidence)
                case = evidence/'case-1';stage = next((case/'builds').glob('build-*'))
                if fault in ['deadline','poll','sequence','pid','identity']:
                    path = stage/'deadline-audit.jsonl';rows = [json.loads(line) for line in path.read_text().splitlines()]
                    if fault == 'deadline': rows[0]['milliseconds'] = 1
                    elif fault == 'poll': next(row for row in rows if row['kind'] == 'target_poll' and row['code'] is not None)['code'] = -15
                    elif fault == 'sequence': rows[1]['sequence'] = 1
                    elif fault == 'pid': next(row for row in rows if row['kind'] == 'target_spawn')['pid'] = 1
                    else: rows[0]['anchor_sha256'] = '0'*64
                    path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
                elif fault == 'frame':
                    path = case/'0-frame.raw';payload = bytearray(path.read_bytes());payload[52] ^= 1;path.write_bytes(payload)
                elif fault == 'verdict':
                    path = case/'result.json';data = json.loads(path.read_text());data['records'][0]['execution']['report']['failure'] = 'deadline';path.write_text(json.dumps(data))
                else:
                    path = case/'closure.json';data = json.loads(path.read_text());data['liveWorkers'] = 1;path.write_text(json.dumps(data))
                files = {str(item.relative_to(evidence)):{'bytes':item.stat().st_size,'sha256':hashlib.sha256(item.read_bytes()).hexdigest()} for item in evidence.rglob('*') if item.is_file() and item.name != 'manifest.json'}
                (evidence/'manifest.json').write_text(json.dumps({'files':files}))
                with self.assertRaises(AssertionError): verify(evidence)
