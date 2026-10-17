"""Evidence rejection must survive Python optimization; never launch native work."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


class CompletionOptimizedAdmissionTests(unittest.TestCase):
    def test_optimized_resealed_faults(self):
        cases = [
            ('verify_completion_guard.py', 'completion-guard-corrected-2026-10-14', 'delayed-zero'),
            ('verify_post_completion_delay.py', 'post-completion-delay-2026-10-14', 'delayed'),
        ]
        code = ('import importlib.util,sys; '
                's=importlib.util.spec_from_file_location("consumer",sys.argv[1]); '
                'm=importlib.util.module_from_spec(s);s.loader.exec_module(m); '
                'm.verify(sys.argv[2])')
        for consumer, folder, mode in cases:
            for fault in ['positive', 'wait', 'drain', 'hash', 'payload', 'terminal-time']:
                with self.subTest(consumer=consumer, fault=fault), tempfile.TemporaryDirectory() as tmp:
                    evidence = Path(tmp)/'evidence'
                    shutil.copytree(ROOT/'research/evidence'/folder, evidence)
                    path = evidence/mode/'result.json'
                    data = json.loads(path.read_text())
                    if fault == 'wait':
                        data['record']['report']['target_code'] = 71
                    elif fault == 'drain':
                        data['record']['report']['drained'] = False
                    elif fault == 'hash':
                        data['record']['stdoutSha256'] = '0'*64
                    elif fault == 'payload':
                        (evidence/mode/'owned.raw').write_bytes(b'bad-data')
                    elif fault == 'terminal-time':
                        audit = evidence/mode/'deadline-audit.jsonl'
                        rows = [json.loads(line) for line in audit.read_text().splitlines()]
                        next(row for row in rows if row['kind'] == 'target_poll' and row['code'] is not None)['value'] = 100.0
                        audit.write_text(''.join(json.dumps(row)+'\n' for row in rows))
                    if fault != 'positive':
                        path.write_text(json.dumps(data))
                        files = {str(p.relative_to(evidence)): {
                            'bytes':p.stat().st_size,
                            'sha256':hashlib.sha256(p.read_bytes()).hexdigest()
                        } for p in evidence.rglob('*') if p.is_file() and p.name != 'manifest.json'}
                        (evidence/'manifest.json').write_text(json.dumps({'files':files}))
                    result = subprocess.run(
                        [sys.executable, '-O', '-B', '-c', code,
                         str(ROOT/'tools/re/tests'/consumer), str(evidence)],
                        capture_output=True, text=True, timeout=10)
                    if fault == 'positive':
                        self.assertEqual(result.returncode, 0, result.stderr)
                    else:
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('AssertionError: Completion evidence rejected', result.stderr)


if __name__ == '__main__':
    unittest.main()
