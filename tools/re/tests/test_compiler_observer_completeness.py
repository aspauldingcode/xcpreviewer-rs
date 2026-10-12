import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from reloop.compilerwitness import CompilerWitness
from reloop.sourcecache import run_compiler
from verify_compiler_observer_completeness import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/compiler-observer-completeness-2026-10-11'
class ObserverCompletenessTests(unittest.TestCase):
 def test_seal_and_reader(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),'882a117baa1726e0126d1a7cef41594a596f703161cbc0f0ae98c15065d37205');self.assertTrue(verify(E)['missing_active_root_rejected'])
  self.assertEqual(hashlib.sha256((E/'compilerwitness-after.py').read_bytes()).hexdigest(),'76d7aacf9dbecde1bcd3e707ed7c9bb89fc3ce3066541a8787ead0aaa313902a')
 def test_resealed_faults(self):
  for fault in ['accepted','error','samples','identity','native','signals','startup']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e)
    if fault in ['native','signals','startup']:
     p=e/'scope.json';d=json.loads(p.read_text());d[{'native':'native_processes','signals':'signals','startup':'native_startup_qualified'}[fault]]={'native':1,'signals':[9],'startup':True}[fault]
    else:
     p=e/'results.json';d=json.loads(p.read_text());r=d['omitted']['after']
     if fault=='accepted':r['accepted']=True
     elif fault=='error':r['error']=None
     elif fault=='samples':r['samples']=4
     else:r['known']['10'][0]+=1
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
 def test_every_requested_root_required_before_identity_commit(self):
  rows={10:{'parent':1,'group':10,'state':'L','identity':(1,2,'/owned')}}
  w=CompilerWitness(lambda roots,known:rows)
  with self.assertRaisesRegex(RuntimeError,'active root missing'):w.sample({10,11})
  self.assertEqual(w.known,{})
 def test_run_compiler_rejects_omission_and_reaps_fake_root(self):
  import subprocess
  rows=iter([{}, {10:{'parent':1,'group':10,'state':'L','identity':(1,2,'/owned')}}, {}]);signals=[]
  class Process:
   pid=10;returncode=None;waits=0
   def poll(self):return self.returncode
   def wait(self,timeout):
    self.waits+=1
    if self.waits==1:raise subprocess.TimeoutExpired(['owned'],timeout)
    self.returncode=0;return 0
  process=Process()
  with patch('reloop.sourcecache.subprocess.Popen',return_value=process),patch('reloop.sourcecache.os.killpg',side_effect=lambda pid,sig:signals.append((pid,sig))):
   with self.assertRaisesRegex(RuntimeError,'active root missing'):run_compiler(['owned'],observer=lambda roots,known:next(rows))
  self.assertEqual(signals,[(10,9)]);self.assertEqual(process.waits,2);self.assertEqual(process.returncode,0)
