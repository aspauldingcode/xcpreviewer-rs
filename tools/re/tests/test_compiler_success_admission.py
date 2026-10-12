import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('admission_reader',Path(__file__).with_name('verify_compiler_success_admission.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class CompilerSuccessAdmissionTests(unittest.TestCase):
 def test_seal_source_and_core(self):
  e=ROOT/'research/evidence/compiler-success-admission-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertTrue(reader.verify(e)['survivor_success_rejected']);self.assertEqual((ROOT/'tools/re/fixtures/CompilerSuccessAdmission/emitter.py').read_bytes(),(e/'emitter.py').read_bytes());self.assertEqual((ROOT/'tools/re/reloop/sourcecache.py').read_bytes(),(e/'sourcecache-after.py').read_bytes())
 def test_resealed_faults(self):
  for fault in ['accepted','late','unfinished','signal','identity','first','later','final','plain','clang','compiler','removed-guard']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/compiler-success-admission-2026-10-11',e);p=e/'survivor/result.json';d=json.loads(p.read_text())
    if fault=='accepted':d['error']=None
    elif fault=='late':d['elapsed_seconds']=2
    elif fault=='unfinished':d['child_finished']=False
    elif fault=='signal':d['kill_signal_used']=True
    elif fault=='identity':q=e/'survivor/root.json';v=json.loads(q.read_text());v['process_group']+=1;q.write_text(json.dumps(v))
    elif fault=='plain':q=e/'plain.json';v=json.loads(q.read_text());v['code']=1;q.write_text(json.dumps(v))
    elif fault=='clang':q=e/'clang.json';v=json.loads(q.read_text());v['code']=1;q.write_text(json.dumps(v))
    elif fault=='compiler':q=e/'clang.json';v=json.loads(q.read_text());v['compiler_sha256']='0'*64;q.write_text(json.dumps(v))
    elif fault=='removed-guard':shutil.copyfile(e/'sourcecache-before.py',e/'sourcecache-after.py')
    else:
     q=e/'survivor'/({'first':'at-rejection.bin','later':'after-rejection.bin','final':'heartbeat.bin'}[fault]);raw=bytearray(q.read_bytes());raw[-1]^=1;q.write_bytes(raw)
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(f.relative_to(e)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in e.rglob('*') if f.is_file() and f.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
 def test_group_presence_permission_and_disappearance_are_read_only(self):
  from reloop.sourcecache import run_compiler
  for effect,error in [(None,RuntimeError),(PermissionError('unobservable'),PermissionError),(ProcessLookupError(),None)]:
   with self.subTest(effect=effect),patch('reloop.sourcecache.subprocess.Popen',return_value=SimpleNamespace(pid=2147483647,wait=lambda timeout:0)),patch('reloop.sourcecache.os.killpg',side_effect=effect) as signals:
    if error:
     with self.assertRaises(error):run_compiler(['owned'],timeout=1)
    else:self.assertEqual(run_compiler(['owned'],timeout=1).returncode,0)
    signals.assert_called_once_with(2147483647,0)

SEAL='0a42a93e9d13c946e91b198388eca852a68c35e2eb57eef9fd268d13f79946a2'
