"""Recorded helper-process faults; never invokes Node, the helper or a child."""
from pathlib import Path
import json,shutil,tempfile,unittest
import admit as a
ROOT=Path(__file__).resolve().parent
class Recorded(unittest.TestCase):
 def clone(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=Path(t.name)/'e';shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns('__pycache__'));return p
 def rewrite(self,p,change):
  q=p/'execution-record.json';run=json.loads(q.read_text());v=json.loads(run['record']['stdout']);change(v);s=json.dumps(v)+'\n';run['record'].update(stdout=s,stdoutBytes=len(s.encode()),stdoutSha256=a.H(s.encode()));q.write_text(json.dumps(run))
 def test_actual_scope(self):
  v=a.observed(ROOT);self.assertEqual(v['marker_bytes_compared'],2048);self.assertTrue(v['default_abort_settles_before_owned_exit_and_late_write']);self.assertFalse(v['provider_target_UI_settlement_qualified'])
 def test_rehashed_marker_padding_tail(self):
  for off in [0,20,1023]:
   p=self.clone();q=p/'owned-documents/default/marker.raw';raw=bytearray(q.read_bytes());raw[off]^=1;q.write_bytes(raw);self.rewrite(p,lambda v:v['rows'][0].update(marker_sha256=a.H(raw)))
   with self.assertRaises(ValueError):a.observed(p)
 def test_rewritten_event_and_child_identity(self):
  for fault in ['event','identity']:
   p=self.clone()
   if fault=='event':self.rewrite(p,lambda v:v['rows'][0].update(marker_present_at_settlement=True))
   else:
    q=p/'owned-documents/default/ready.json';v=json.loads(q.read_text());v['ppid']=True;q.write_text(json.dumps(v))
   with self.assertRaises(ValueError):a.observed(p)
 def test_typed_lifecycle_and_deadline(self):
  for fault in ['exit','remaining','deadline']:
   p=self.clone()
   if fault=='deadline':q=p/'execution-outer.json';v=json.loads(q.read_text());v['completed_at']='2026-10-19T17:31:00+00:00'
   else:q=p/'execution-record.json';v=json.loads(q.read_text());v['record']['report']['target_code' if fault=='exit' else 'remaining_observed']=False
   q.write_text(json.dumps(v))
   with self.assertRaises(ValueError):a.observed(p)
if __name__=='__main__':unittest.main()
