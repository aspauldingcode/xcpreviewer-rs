"""Recorded output tampering controls, never executes Node or WASM."""
from pathlib import Path
import json
import shutil
import tempfile
import unittest
import admit as a
ROOT=Path(__file__).resolve().parent
class Recorded(unittest.TestCase):
 def clone(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=Path(t.name)/'e';shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns('__pycache__'));return p
 def test_actual_complete_predictions(self):
  r=a.admit(ROOT);self.assertEqual(r['all_bytes_compared'],524288);self.assertTrue(r['zero_growth_detaches']);self.assertTrue(r['failed_growth_preserves_buffer']);self.assertFalse(r['canvas_qualified'])
 def test_rehashed_padding_tail_and_new_page(self):
  for stage,offset in [('initial',68),('initial',65535),('positive-grow',65541),('wasm-failed-grow',131071)]:
   with self.subTest(stage=stage,offset=offset):
    p=self.clone();q=p/'execution.json';run=json.loads(q.read_text());v=json.loads(run['stdout']);row=next(x for x in v['rows'] if x['stage']==stage);rawfile=p/'owned-output'/row['file'];raw=bytearray(rawfile.read_bytes());raw[offset]^=1;rawfile.write_bytes(raw);row['sha256']=a.H(raw);run['stdout']=json.dumps(v)+'\n';q.write_text(json.dumps(run))
    with self.assertRaises(ValueError):a.admit(p)
 def test_rewritten_lifecycle_and_terminal_fields(self):
  for kind in ['event','exit','deadline','rea']:
   with self.subTest(kind=kind):
    p=self.clone();q=p/'execution.json';run=json.loads(q.read_text())
    if kind=='event':
     v=json.loads(run['stdout']);v['events'][0]['old_buffer_bytes']=False;run['stdout']=json.dumps(v)+'\n';q.write_text(json.dumps(run))
    elif kind=='exit':run['exit']=False;q.write_text(json.dumps(run))
    elif kind=='deadline':run['completed_at']='2026-10-19T17:01:00+00:00';q.write_text(json.dumps(run))
    else:
     q=p/'rea-identity.json';v=json.loads(q.read_text());v['closed']=False;q.write_text(json.dumps(v))
    with self.assertRaises(ValueError):a.admit(p)
if __name__=='__main__':unittest.main()
