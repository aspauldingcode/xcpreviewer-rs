import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from reloop.compilerwitness import CompilerWitness
from reloop.sourcecache import run_compiler
from verify_compiler_descendant_retirement import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/compiler-descendant-retirement-2026-10-11'
ROWS={10:{'parent':1,'group':10,'state':'L','identity':(1,2,'/owned/root')},11:{'parent':10,'group':11,'state':'L','identity':(3,4,'/owned/child')}}
class DescendantRetirementTests(unittest.TestCase):
 def test_seal_and_reader(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(verify(E)['missing_final_descendant_rejected']);self.assertEqual((ROOT/'tools/re/reloop/compilerwitness.py').read_bytes(),(E/'compilerwitness-after.py').read_bytes())
 def test_resealed_faults(self):
  for fault in ['accepted','error','identity','old-accepted','zombie-rejected','native','signals','reclaim']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e)
    if fault in ['native','signals','reclaim']:
     p=e/'scope.json';d=json.loads(p.read_text());d[{'native':'native_processes','signals':'native_signals','reclaim':'physical_reclaim_observed'}[fault]]={'native':1,'signals':[9],'reclaim':True}[fault]
    else:
     p=e/'results.json';d=json.loads(p.read_text());r=d['missing']['after']
     if fault=='accepted':r['accepted']=True
     elif fault=='error':r['error']=None
     elif fault=='identity':r['known']['11'][0]+=1
     elif fault=='old-accepted':d['missing']['before']['accepted']=False
     else:d['zombie']['after']['accepted']=False
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
 def test_source_replay_old_vs_new(self):
  for phase in ['before','after']:
   ns={};exec((E/('compilerwitness-'+phase+'.py')).read_bytes(),ns);it=iter([ROWS,{}]);w=ns['CompilerWitness'](lambda roots,known:next(it));w.sample({10})
   if phase=='before':w.admit(10)
   else:
    with self.assertRaisesRegex(RuntimeError,'retirement was not observed'):w.admit(10)
 def test_matching_zombie_passes_live_and_reused_birth_reject(self):
  for state,birth,accept in [('Z',3,True),('L',3,False),('Z',5,False)]:
   it=iter([ROWS,{11:dict(ROWS[11],parent=1,state=state,identity=(birth,4,'/owned/child'))}]);w=CompilerWitness(lambda roots,known:next(it));w.sample({10})
   if accept:w.admit(10)
   else:
    with self.assertRaises(RuntimeError):w.admit(10)
 def test_all_known_children_need_final_rows(self):
  rows=dict(ROWS);rows[12]=dict(ROWS[11],identity=(7,8,'/owned/other'));final={11:dict(ROWS[11],state='Z')};it=iter([rows,final]);w=CompilerWitness(lambda roots,known:next(it));w.sample({10})
  with self.assertRaisesRegex(RuntimeError,'retirement was not observed'):w.admit(10)
 def test_run_compiler_final_missing_rejects_without_cleanup_signal(self):
  it=iter([{},ROWS,{}]);calls=[]
  class Process:
   pid=10;returncode=None
   def poll(self):return self.returncode
   def wait(self,timeout):self.returncode=0;return 0
  process=Process()
  with patch('reloop.sourcecache.subprocess.Popen',return_value=process),patch('reloop.sourcecache.os.killpg',side_effect=lambda pid,sig:calls.append((pid,sig))):
   with self.assertRaisesRegex(RuntimeError,'retirement was not observed'):run_compiler(['owned'],observer=lambda roots,known:next(it))
  self.assertEqual(process.returncode,0);self.assertEqual(calls,[])
SEAL='bd414edcc4e5e66c63c901d042e6bfa59db81a0561f19d521900950db84fd7b3'
