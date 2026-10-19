"""Recorded Linux faults; never starts Docker or a WASM runtime."""
from pathlib import Path
import json,shutil,tempfile,unittest
import admit as old
from admit_recorded import observed
ROOT=Path(__file__).resolve().parent
class Recorded(unittest.TestCase):
 def clone(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=Path(t.name)/'e';shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns('__pycache__'));return p
 def test_actual_scope(self):
  v=observed(ROOT);self.assertEqual(v['independent_bytes_compared'],524288);self.assertEqual(v['producer_relation_bytes'],524288);self.assertTrue(v['owned_cleanup_verified']);self.assertFalse(v['js_host_view_semantics_measured'])
 def test_original_boolean_inspect_acceptance_retained(self):
  p=self.clone();q=p/'container-cleanup.json';v=json.loads(q.read_text());v['inspect_exit']=False;q.write_text(json.dumps(v))
  self.assertTrue(old.observed(p)['linux_core_memory_verified'])
  with self.assertRaisesRegex(ValueError,'typed inspect exit'):observed(p)
 def test_rehashed_complete_bytes(self):
  for stage,offset in [('initial',68),('initial',65535),('positive-grow',65541),('wasm-failed-grow',131071)]:
   with self.subTest(stage=stage,offset=offset):
    p=self.clone();q=p/'owned-output'/(stage+'.raw');raw=bytearray(q.read_bytes());raw[offset]^=1;q.write_bytes(raw);q=p/'owned-output/result.json';v=json.loads(q.read_text());next(row for row in v['rows'] if row['stage']==stage)['sha256']=old.H(raw);q.write_text(json.dumps(v))
    with self.assertRaises(ValueError):observed(p)
 def test_lifecycle_command_terminal_and_cleanup(self):
  for fault in ['event','exit','deadline','command','remaining','inventory','runtime']:
   with self.subTest(fault=fault):
    p=self.clone()
    if fault=='event':q=p/'owned-output/result.json';v=json.loads(q.read_text());v['events'][2]['error']='RangeError'
    elif fault in ['remaining','inventory']:
     q=p/('container-cleanup.json' if fault=='remaining' else 'existing-containers.json');v=json.loads(q.read_text());v['remaining_exit' if fault=='remaining' else 'existing_preserved']=False
    elif fault=='runtime':q=p/'runtime-validation.json';v=json.loads(q.read_text());v['after']=False
    else:
     q=p/'execution.json';v=json.loads(q.read_text())
     if fault=='exit':v['exit']=False
     elif fault=='deadline':v['completed_at']='2026-10-19T17:21:00+00:00'
     else:v['command']=['docker','run','unreviewed']
    q.write_text(json.dumps(v))
    with self.assertRaises(ValueError):observed(p)
if __name__=='__main__':unittest.main()
