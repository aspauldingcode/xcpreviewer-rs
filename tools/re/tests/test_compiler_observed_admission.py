import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('observed_admission_reader',Path(__file__).with_name('verify_compiler_observed_admission.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class CompilerObservedAdmissionTests(unittest.TestCase):
 def test_seal_source_and_fixture(self):
  e=ROOT/'research/evidence/compiler-observed-admission-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertFalse(reader.verify(e)['native_post_root_observer_qualified'])
  for filename in ['sourcecache','compilerwitness']:self.assertEqual((ROOT/'tools/re/reloop'/f'{filename}.py').read_bytes(),(e/('sourcecache-after.py' if filename=='sourcecache' else 'compilerwitness.py')).read_bytes())
  self.assertEqual((ROOT/'tools/re/fixtures/CompilerObservedAdmission/emitter.py').read_bytes(),(e/'emitter.py').read_bytes())
 def test_resealed_faults(self):
  for fault in ['default-exit','false-qualified','retried','missing-growth','byte','birth','same-path','ancestry','group','helper']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/compiler-observed-admission-2026-10-11',e)
    if fault=='default-exit':p=e/'group-only/result.json';d=json.loads(p.read_text());d['code']=1;p.write_text(json.dumps(d))
    elif fault in ['false-qualified','retried']:p=e/'retained-failure.json';d=json.loads(p.read_text());d['qualified_observed_success_admission' if fault=='false-qualified' else 'producer_retry']=True;p.write_text(json.dumps(d))
    elif fault=='missing-growth':p=e/'observed/after-return.bin';shutil.copyfile(e/'observed/at-return.bin',p)
    elif fault=='byte':p=e/'group-only/heartbeat.bin';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b)
    elif fault=='helper':p=e/'environment.json';d=json.loads(p.read_text());d['observer_binary_sha256']='0'*64;p.write_text(json.dumps(d))
    else:
     p=e/'observer-samples.json';d=json.loads(p.read_text());root=d[2]['roots'][0];row=d[2]['rows'][str(root)];child=next(x for x in d[2]['rows'] if x!=str(root))
     if fault=='birth':row['identity'][0]+=1
     elif fault=='same-path':row['identity'][2]=d[1]['rows'][str(root)]['identity'][2]
     elif fault=='ancestry':d[2]['rows'][child]['parent']+=1
     elif fault=='group':d[2]['rows'][child]['group']=root
     p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
 def test_native_root_exec_rows_refresh_then_model_detached_rejection(self):
  from reloop.compilerwitness import CompilerWitness
  e=ROOT/'research/evidence/compiler-observed-admission-2026-10-11';samples=json.loads((e/'observer-samples.json').read_text());root=samples[1]['roots'][0]
  rows=[{int(pid):row for pid,row in s['rows'].items()} for s in samples];child={pid:row for pid,row in rows[2].items() if pid!=root};it=iter([rows[0],rows[1],rows[2],child]);w=CompilerWitness(lambda roots,known:next(it));w.sample(set());w.sample({root});w.sample({root})
  self.assertEqual(w.known[root],tuple(rows[2][root]['identity']))
  with self.assertRaisesRegex(RuntimeError,'descendants remain'):w.admit(root)
 def test_identity_mutation_malformed_and_budget_reject(self):
  from reloop.compilerwitness import CompilerWitness
  good={10:{'parent':1,'group':10,'state':'L','identity':(1,2,'/owned')}}
  for mutate in ['birth','path','state']:
   w=CompilerWitness(lambda roots,known:good);w.sample({10});bad={10:dict(good[10])}
   if mutate=='birth':bad[10]['identity']=(2,2,'/owned')
   elif mutate=='path':bad[10]['identity']=(1,2,'/replacement')
   else:bad[10]['state']='?'
   w.observer=lambda roots,known:bad
   with self.assertRaises((RuntimeError,ValueError)):w.sample(set())
  w=CompilerWitness(lambda roots,known:{});w.samples=64
  with self.assertRaisesRegex(RuntimeError,'budget'):w.sample(set())
 def test_invalid_observer_fails_before_launch(self):
  from reloop.sourcecache import run_compiler
  with patch('reloop.sourcecache.subprocess.Popen') as launch:
   with self.assertRaises(ValueError):run_compiler(['owned'],observer=42)
   launch.assert_not_called()

SEAL='d96f5c372b0ed577a176ce68d11cb079e223dde0c816eee0697f9f2aa291513a'
