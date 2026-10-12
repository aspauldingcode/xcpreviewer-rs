import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('ready_reader',Path(__file__).with_name('verify_observer_ready_admission.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class ObserverReadyAdmissionTests(unittest.TestCase):
 def test_seal_implementation_and_fixture(self):
  e=ROOT/'research/evidence/observer-ready-admission-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(reader.verify(e)['ready_gated_post_root_rejection_verified']);self.assertEqual((ROOT/'tools/re/fixtures/ObserverReadyAdmission/emitter.py').read_bytes(),(e/'emitter.py').read_bytes())
  for name in ['sourcecache','compilerwitness']:self.assertEqual((ROOT/'tools/re/reloop'/(name+'.py')).read_bytes(),(e/(name+'.py')).read_bytes())
 def test_resealed_faults(self):
  for fault in ['root-exit','accepted','old-error','clean','ready','birth','parent','group','zombie','signal','heartbeat','retirement','missing-final','path']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/observer-ready-admission-2026-10-11',e)
    if fault in ['root-exit','accepted','old-error','clean']:
     p=e/('clean/result.json' if fault=='clean' else 'detached/result.json');d=json.loads(p.read_text())
     if fault=='root-exit':d['root_exit_code']=42
     elif fault=='accepted':d['code']=0
     elif fault=='old-error':d['error']='Compiler observed lifetime identity changed'
     else:d['code']=42
     p.write_text(json.dumps(d))
    elif fault=='signal':p=e/'signals.json';d=json.loads(p.read_text());d[0]['signal']=9;p.write_text(json.dumps(d))
    elif fault=='heartbeat':p=e/'detached/after-rejection.bin';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b)
    elif fault=='retirement':p=e/'retirement.json';d=json.loads(p.read_text());d['live_owned_child']=True;p.write_text(json.dumps(d))
    else:
     p=e/'samples.json';d=json.loads(p.read_text());indices=[i for i,s in enumerate(d) if s['mode']=='detached'];last=d[indices[-1]];child=next(iter(last['rows']));live=next(s for s in d if s['mode']=='detached' and s['roots'])
     if fault=='ready':live['ready']['pid']+=1
     elif fault=='birth':last['rows'][child]['identity'][0]+=1
     elif fault=='parent':last['rows'][child]['parent']=json.loads((e/'detached/ready.json').read_text())['pid']
     elif fault=='group':last['rows'][child]['group']+=1
     elif fault=='zombie':last['rows'][child]['state']='Z'
     elif fault=='missing-final':del d[indices[-1]]
     elif fault=='path':live['ready']['executable']='/wrong-executable'
     p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='f7d5dc35531193472a97dfec719f5bebe102aeff0b07c393171c380511ebeb70'
