"""Recorded acquisition faults; never executes the native source/binary."""
from pathlib import Path
import json
import shutil
import tempfile
import unittest
import compare as c
from acquire import observed
ROOT=Path(__file__).resolve().parent
class Recorded(unittest.TestCase):
    def clone(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=Path(t.name)/'e'
        shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns('probe','__pycache__'));return p
    def test_numerical_rejections_remain(self):
        v=observed(ROOT);self.assertTrue(v['native_acquisition_qualified']);self.assertTrue(v['linear_identity_control'])
        self.assertEqual(v['all_bytes_compared'],172416)
        self.assertEqual(v['routes'][0]['identity']['mismatch_bytes'],702)
        self.assertEqual(v['routes'][0]['historical_8bit_relation']['mismatch_bytes'],9540)
        self.assertFalse(v['canvas_qualified'])
    def test_rehashed_complete_bytes(self):
        for provider,offset in [(True,12288),(False,12288),(False,49151)]:
            with self.subTest(provider=provider,offset=offset):
                p=self.clone();q=p/'fixture-record.json';v=json.loads(q.read_text());rows=[json.loads(s) for s in v['record']['stdout'].splitlines()]
                name=rows[0]['provider_file' if provider else 'file'];path=p/'owned-documents'/name;raw=bytearray(path.read_bytes());raw[offset]^=1;path.write_bytes(raw)
                rows[0]['provider_sha256' if provider else 'sha256']=c.digest(raw)
                stdout=''.join(json.dumps(row)+'\n' for row in rows);v['record'].update(stdout=stdout,stdoutBytes=len(stdout.encode()),stdoutSha256=c.digest(stdout.encode()));q.write_text(json.dumps(v))
                with self.assertRaises(ValueError):observed(p)
    def test_typed_lifecycle_and_deadline(self):
        for field in ['remaining_observed','target_code']:
            p=self.clone();q=p/'fixture-record.json';v=json.loads(q.read_text());v['record']['report'][field]=False;q.write_text(json.dumps(v))
            with self.assertRaises(ValueError):observed(p)
        p=self.clone();q=p/'completed.json';v=json.loads(q.read_text());v['completed_at']='2026-10-19T16:49:00+00:00';q.write_text(json.dumps(v))
        with self.assertRaises(ValueError):observed(p)
if __name__=='__main__':unittest.main()
