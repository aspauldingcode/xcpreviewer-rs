import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('stable_reader',Path(__file__).with_name('verify_observer_stable_diagnostic.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class ObserverStableDiagnosticTests(unittest.TestCase):
 def test_seal_fixture_and_independent_identity(self):
  e=ROOT/'research/evidence/observer-stable-diagnostic-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['independent_parent_group_dyld_checks'],4);self.assertEqual((ROOT/'tools/re/fixtures/ObserverStableDiagnostic/child.py').read_bytes(),(e/'child.py').read_bytes())
 def test_resealed_faults(self):
  for fault in ['exit','stdout','popen','controller','marker','missing','error','birth','path','parent','group','state','helper']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/observer-stable-diagnostic-2026-10-11',e)
    if fault in ['exit','stdout','popen','controller']:
     p=e/'wait.json';d=json.loads(p.read_text())
     if fault=='exit':d['code']=42
     elif fault=='stdout':d['stdout']='failed'
     else:d['spawn']['popen_pid' if fault=='popen' else 'controller_pid']+=1
     p.write_text(json.dumps(d))
    elif fault=='marker':p=e/'child/finished.bin';p.write_bytes(b'finisheD')
    elif fault=='helper':p=e/'environment.json';d=json.loads(p.read_text());d['observer_binary_sha256']='0'*64;p.write_text(json.dumps(d))
    else:
     p=e/'samples.json';d=json.loads(p.read_text());sample=d[3];target=str(sample['target']);row=sample['rows'][target]
     if fault=='missing':del sample['rows'][target]
     elif fault=='error':sample['error']={'type':'OSError','message':'unavailable'}
     elif fault=='birth':row['identity'][0]+=1
     elif fault=='path':row['identity'][2]='/wrong-executable'
     elif fault=='parent':row['parent']+=1
     elif fault=='group':row['group']+=1
     elif fault=='state':row['state']='Z'
     p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='670858535c2725ab9ceca4d902486ddbe729037e805a73726d831ab777cb7a7b'
