"""Synthetic records only; no process or native receipt observation."""
import unittest,tempfile,shutil,json,subprocess,sys
from pathlib import Path
from decoder import expected,canonical,filename
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name)
  for n in ['validate_receipts.py','decoder.py']:shutil.copy2(Path(__file__).parent/n,self.p/n)
  self.path='/owned/PreviewLab.app/Contents/MacOS/PreviewLab';self.ident={'pid':1234,'nonce':'a'*32,'view':'01234567-89ab-cdef-0123-456789abcdef'};self.live={'pid':1234,'state':'L','identity':[1,2,self.path]}
  self.write('experiment.json',{'nonce':'a'*32,'expected_binary_path':self.path,'expected_filelist_utf8':'owned.swift\n','source_sha256':'s'})
  self.write('build-association.json',{'binary_path':self.path,'filelist_utf8':'owned.swift\n','source_sha256':'s'})
 def write(self,n,v):(self.p/n).write_text(json.dumps(v))
 def observation(self,stage,live=None):
  rows=[]
  for i in range(stage):
   v=expected(self.ident,'appear' if i==0 else 'increment',i,i);rows.append({'name':filename(v),'raw_hex':canonical(v).hex(),'live_identity':live or self.live})
  self.write('receipt-observation-%d.json'%stage,{'records':rows})
 def run_stage(self,stage):return subprocess.run([sys.executable,*(['-O'] if sys.flags.optimize else []),'-B',str(self.p/'validate_receipts.py'),str(stage),self.ident['view']],capture_output=True,timeout=3).returncode
 def test_positive_finite_transcript(self):
  self.observation(1);self.assertEqual(self.run_stage(1),0);self.observation(2);self.assertEqual(self.run_stage(2),0)
 def test_same_suffix_other_path(self):
  v={**self.live,'identity':[1,2,'/other/PreviewLab.app/Contents/MacOS/PreviewLab']};self.observation(1,v);self.assertNotEqual(self.run_stage(1),0)
 def test_wrong_source_association(self):
  self.observation(1);self.write('build-association.json',{'binary_path':self.path,'filelist_utf8':'other.swift\n','source_sha256':'s'});self.assertNotEqual(self.run_stage(1),0)
 def test_changed_lifetime(self):
  self.observation(1);self.assertEqual(self.run_stage(1),0);self.observation(2,{**self.live,'identity':[3,2,self.path]});self.assertNotEqual(self.run_stage(2),0)
 def test_boolean_pid(self):
  self.observation(1,{**self.live,'pid':True});self.assertNotEqual(self.run_stage(1),0)
 def test_incomplete_transcript(self):
  self.observation(1);self.assertEqual(self.run_stage(1),0);self.write('receipt-observation-2.json',{'records':[]});self.assertNotEqual(self.run_stage(2),0)
if __name__=='__main__':unittest.main()
