"""Synthetic acquisition gates only; no JSContext or native execution."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import admit as a
import test_byte_compare as t
ROOT=Path(__file__).resolve().parent
class Gates(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name)
  for name in a.parsed((ROOT/'approved-pins.json').read_text()):shutil.copy2(ROOT/name,self.p/name)
  shutil.copy2(ROOT/'approved-pins.json',self.p/'approved-pins.json')
  fixture=t.Tests();fixture.setUp();self.addCleanup(fixture.tmp.cleanup);shutil.copytree(fixture.p/'owned-documents',self.p/'owned-documents')
  value=fixture.v;f=a.parsed((self.p/'framework-before.json').read_text())
  value.update(engine='public JavaScriptCore JSContext',native_UI_execution=False,non_Apple_OS_verified=False,canvas_qualified=False,environment={'framework_identifier':f['identifier'],'framework_version':f['version'],'framework_path':'/System/Library/Frameworks/JavaScriptCore.framework','machine':'arm64','system':'Darwin'})
  value['engine_exports']=[dict(e,type={'synthetic':True}) for e in value['exports']]
  source=a.digest(self.p/'probe.c');binary='a'*64;execution='/private/tmp/jsc-memory-growth-20261019'
  for i,phase in enumerate(['compile','output-valid','fixture']):
   stdout='' if phase=='compile' else json.dumps({'pid':123,'status':'owned_output_control'})+'\n' if phase=='output-valid' else json.dumps(value)+'\n';stderr='' if phase=='compile' else 'owned_tree_pid:123\n'
   args=['clang','-x','objective-c','-fobjc-arc','-framework','Foundation','-framework','JavaScriptCore',execution+'/probe.c','-o',execution+'/probe'] if phase=='compile' else ['--output-control','output-valid'] if phase=='output-valid' else ['--fixture',execution+'/owned-documents']
   record={'report':{'kind':'complete','target_code':0,'failure':None,'drained':True,'remaining_observed':0},'emergencyClosed':False,'privateAbortRequested':False,'stdout':stdout,'stderr':stderr,'stdoutBytes':len(stdout.encode()),'stdoutSha256':a.b.H(stdout.encode()),'stderrBytes':len(stderr.encode()),'stderrSha256':a.b.H(stderr.encode())}
   self.write(phase+'-record.json',{'phase':phase,'command':'/usr/bin/xcrun' if phase=='compile' else execution+'/probe','args':args,'source_sha256':source,'binary_sha256':binary,'error':None,'record':record});self.write(phase+'-outer.json',{'node_exit':0})
   self.write(phase+'-started.json',{'phase':phase,'started_at':'2026-10-19T17:05:0%d+00:00'%i,'deadline_utc':'2026-10-19T17:10:00Z'})
  self.write('completed.json',{'completed_at':'2026-10-19T17:05:03+00:00','deadline_utc':'2026-10-19T17:10:00Z'})
  self.write('rea-identity.json',{'owned_binary_sha256':binary,'architecture':'arm64','closed':True})
 def write(self,n,v):(self.p/n).write_text(json.dumps(v))
 def test_positive(self):
  v=a.observed(self.p);self.assertTrue(v['second_engine_verified']);self.assertEqual(v['producer_relation_bytes'],524288);self.assertFalse(v['canvas_qualified'])
 def test_terminal_types_and_missing_receipt(self):
  q=self.p/'fixture-record.json';original=q.read_bytes()
  for field in ['target_code','remaining_observed']:
   v=json.loads(original);v['record']['report'][field]=False;self.write(q.name,v)
   with self.assertRaises(ValueError):a.observed(self.p)
  q.write_bytes(original);(self.p/'output-valid-outer.json').unlink()
  with self.assertRaises(ValueError):a.observed(self.p)
 def test_late_and_wrong_artifact(self):
  q=self.p/'completed.json';original=q.read_bytes();v=json.loads(original);v['completed_at']='2026-10-19T17:11:00+00:00';self.write(q.name,v)
  with self.assertRaises(ValueError):a.observed(self.p)
  q.write_bytes(original);v=json.loads((self.p/'rea-identity.json').read_text());v['closed']=False;self.write('rea-identity.json',v)
  with self.assertRaises(ValueError):a.observed(self.p)
 def test_source_pin_and_command(self):
  q=self.p/'fixture-record.json';original=q.read_bytes();v=json.loads(original);v['args']=['--fixture','/unowned'];self.write(q.name,v)
  with self.assertRaises(ValueError):a.observed(self.p)
  q.write_bytes(original)
  with (self.p/'probe.js').open('a') as f:f.write('\n// drift\n')
  with self.assertRaises(ValueError):a.observed(self.p)
if __name__=='__main__':unittest.main()
