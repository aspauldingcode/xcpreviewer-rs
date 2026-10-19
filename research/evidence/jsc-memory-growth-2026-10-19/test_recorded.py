"""Recorded JSC acquisition faults; never executes the engine or native source."""
from pathlib import Path
import json
import shutil
import tempfile
import unittest
import admit as a
ROOT=Path(__file__).resolve().parent
class Recorded(unittest.TestCase):
 def clone(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=Path(t.name)/'e';shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns('probe','__pycache__'));return p
 def rewrite(self,p,change):
  q=p/'fixture-record.json';run=json.loads(q.read_text());v=json.loads(run['record']['stdout']);change(v);s=json.dumps(v)+'\n';run['record'].update(stdout=s,stdoutBytes=len(s.encode()),stdoutSha256=a.b.H(s.encode()));q.write_text(json.dumps(run))
 def test_actual_full_bytes_and_engine_scope(self):
  r=a.observed(ROOT);self.assertEqual(r['all_bytes_compared'],524288);self.assertEqual(r['producer_relation_bytes'],524288);self.assertTrue(r['second_engine_verified']);self.assertFalse(r['browser_verified']);self.assertFalse(r['canvas_qualified'])
 def test_rehashed_complete_bytes(self):
  for stage,offset in [('initial',68),('initial',65535),('positive-grow',65541),('wasm-failed-grow',131071)]:
   with self.subTest(stage=stage,offset=offset):
    p=self.clone();f=p/'owned-documents'/(stage+'.raw');raw=bytearray(f.read_bytes());raw[offset]^=1;f.write_bytes(raw)
    self.rewrite(p,lambda v:next(row for row in v['rows'] if row['stage']==stage).update(sha256=a.b.H(raw)))
    with self.assertRaises(ValueError):a.observed(p)
 def test_rewritten_events_and_framework(self):
  for fault in ['event','framework','descriptor']:
   with self.subTest(fault=fault):
    p=self.clone()
    def change(v):
     if fault=='event':v['events'][0]['old_buffer_bytes']=False
     elif fault=='framework':v['environment']['framework_version']='wrong'
     else:v['engine_exports'][0]['name']='wrong'
    self.rewrite(p,change)
    with self.assertRaises(ValueError):a.observed(p)
 def test_typed_receipts_and_deadline(self):
  for fault in ['exit','remaining','deadline']:
   with self.subTest(fault=fault):
    p=self.clone()
    if fault=='deadline':
     q=p/'completed.json';v=json.loads(q.read_text());v['completed_at']='2026-10-19T17:11:00+00:00';q.write_text(json.dumps(v))
    else:
     q=p/'fixture-record.json';v=json.loads(q.read_text());v['record']['report']['target_code' if fault=='exit' else 'remaining_observed']=False;q.write_text(json.dumps(v))
    with self.assertRaises(ValueError):a.observed(p)
if __name__=='__main__':unittest.main()
