import unittest,tempfile,shutil,json,hashlib,importlib.util
from pathlib import Path
root=Path(__file__).resolve().parent;sp=importlib.util.spec_from_file_location('recorded',root/'verify-recorded.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
class Tests(unittest.TestCase):
 def test_positive(self):self.assertEqual(v.verify(root)['full_bytes_compared'],65536)
 def clone(self,t):
  p=Path(t)/'e';shutil.copytree(root,p,ignore=shutil.ignore_patterns('probe','__pycache__'));return p
 def test_recorded_pixel_padding_tail(self):
  for offset in [0,4096,12480,16383]:
   with self.subTest(offset=offset),tempfile.TemporaryDirectory() as t:
    p=self.clone(t);q=p/'owned-documents'/'wasm-multiply.raw';b=bytearray(q.read_bytes());b[offset]^=1;q.write_bytes(b)
    with self.assertRaises(ValueError):v.verify(p)
 def test_typed_and_lifecycle(self):
  for fault in ['typed','wait_boolean','remaining_boolean','outer_false','late','start_after_completion']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as t:
    p=self.clone(t);q=p/'fixture-record.json';r=json.loads(q.read_text())
    if fault=='typed':
     o=json.loads(r['record']['stdout']);o['exports'][0]['type']['results']=['f32'];s=json.dumps(o)+'\n';r['record'].update(stdout=s,stdoutBytes=len(s.encode()),stdoutSha256=hashlib.sha256(s.encode()).hexdigest());q.write_text(json.dumps(r))
    elif fault in ['wait_boolean','remaining_boolean']:
     r['record']['report']['target_code' if fault=='wait_boolean' else 'remaining_observed']=False;q.write_text(json.dumps(r))
    elif fault=='outer_false':
     q=p/'fixture-outer.json';o=json.loads(q.read_text());o['node_exit']=False;q.write_text(json.dumps(o))
    else:
     q=p/('completed.json' if fault=='late' else 'fixture-started.json');o=json.loads(q.read_text());o['completed_at' if fault=='late' else 'started_at']='2026-10-19T09:56:00+00:00';q.write_text(json.dumps(o))
    with self.assertRaises(ValueError):v.verify(p)
if __name__=='__main__':unittest.main()
