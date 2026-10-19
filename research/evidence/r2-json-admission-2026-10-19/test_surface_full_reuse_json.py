"""Offline resealed JSON counterexamples; no native execution."""
import hashlib,importlib.util,json,shutil,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'research/evidence/surface-full-reuse-2026-10-11'
FAULTS=['positive','generation_bool','generation_float','duplicate_manifest','duplicate_compile','duplicate_wait','duplicate_row','duplicate_peer_generation','duplicate_peer_audit','duplicate_environment','duplicate_rea','nonfinite_nan','nonfinite_infinity','nonfinite_overflow']
def reseal(e):
 (e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
def inject(p,key,raw):
 text=p.read_text();p.write_text('{'+json.dumps(key)+':'+raw+','+text.lstrip()[1:])
def case(e,fault):
 shutil.copytree(SOURCE,e)
 if fault in ['generation_bool','generation_float']:
  p=e/'reuse/receiver.json';v=json.loads(p.read_text());v['fixture_generations']=[True,2] if fault=='generation_bool' else [1,2.0];p.write_text(json.dumps(v))
 elif fault=='duplicate_compile':inject(e/'compile.json','code','9')
 elif fault=='duplicate_wait':inject(e/'wait.json','code','9')
 elif fault=='duplicate_row':
  p=e/'wait.json';v=json.loads(p.read_text());rows=v['stdout'].splitlines();rows[0]='{"mode":"contradictory",'+rows[0].lstrip()[1:];v['stdout']='\n'.join(rows)+'\n';p.write_text(json.dumps(v))
 elif fault=='duplicate_peer_generation':inject(e/'reuse/receiver.json','fixture_generations','[2,1]')
 elif fault=='duplicate_peer_audit':inject(e/'reuse/receiver.json','audit_peer_verified','false')
 elif fault=='duplicate_environment':inject(e/'environment.json','helper_sha256','"contradictory"')
 elif fault=='duplicate_rea':inject(e/'rea.json','open','null')
 elif fault.startswith('nonfinite_'):inject(e/'reuse/receiver.json','unused_debug',{'nonfinite_nan':'NaN','nonfinite_infinity':'Infinity','nonfinite_overflow':'1e999'}[fault])
 reseal(e)
 if fault=='duplicate_manifest':inject(e/'manifest.json','files','{}')
def run(verifier):
 spec=importlib.util.spec_from_file_location('reader',verifier);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);results=[]
 for fault in FAULTS:
  with tempfile.TemporaryDirectory(prefix='r2-json-') as d:
   e=Path(d)/'e';case(e,fault)
   try:result=module.verify(e);accepted=True;error=None
   except (ValueError,AssertionError,KeyError,TypeError) as ex:result=None;accepted=False;error=type(ex).__name__
   results.append({'fault':fault,'accepted':accepted,'error':error,'result':result})
 return {'optimized':not __debug__,'verifier':str(verifier),'cases':results,'native_execution':False}
import unittest,subprocess
class JsonReuseEvidenceTests(unittest.TestCase):
 def test_generation_types_and_unambiguous_finite_json(self):
  result=run(Path(__file__).with_name('verify_surface_full_reuse.py'))
  for row in result['cases']:
   with self.subTest(fault=row['fault']):self.assertIs(row['accepted'],row['fault']=='positive')
 @unittest.skipIf(not __debug__, 'Already running optimized matrix')
 def test_same_matrix_under_optimization(self):
  child=subprocess.run([sys.executable,'-O','-B',__file__],capture_output=True,text=True,timeout=20)
  self.assertEqual(child.returncode,0,child.stdout+child.stderr)
if __name__=='__main__':unittest.main()
