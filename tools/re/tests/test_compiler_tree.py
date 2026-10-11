import hashlib,importlib.util,json,shutil,tempfile,unittest,subprocess,signal
from pathlib import Path
from unittest.mock import patch,Mock
from reloop import sourcecache
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('compiler_tree_reader',Path(__file__).with_name('verify_compiler_tree.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class CompilerTreeTests(unittest.TestCase):
 def test_sealed_owned_timeout_and_current_builder(self):
  e=ROOT/'research/evidence/compiler-tree-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['heartbeat_bytes'],32);self.assertEqual((ROOT/'tools/re/reloop/sourcecache.py').read_bytes(),(e/'fixed-sourcecache.py').read_bytes())
 def test_timeout_group_kill_and_descriptor_close(self):
  child=Mock(pid=42000);child.wait.side_effect=[subprocess.TimeoutExpired(['owned'],0.4),-9];files=[];real=sourcecache.tempfile.TemporaryFile
  def opened():f=real();files.append(f);return f
  with patch.object(sourcecache.tempfile,'TemporaryFile',side_effect=opened),patch.object(sourcecache.subprocess,'Popen',return_value=child) as spawn,patch.object(sourcecache.os,'killpg') as kill:
   with self.assertRaises(subprocess.TimeoutExpired):sourcecache.run_compiler(['owned'],timeout=0.4)
   self.assertTrue(spawn.call_args.kwargs['start_new_session']);kill.assert_called_once_with(42000,signal.SIGKILL);self.assertEqual(child.wait.call_count,2)
  self.assertTrue(all(f.closed for f in files))
 def test_resealed_faults(self):
  for fault in ['exit','error','reaped','owner','group','continued','stable','done']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/compiler-tree-2026-10-11',e);root=e/'fixed';p=root/'wait.json';d=json.loads(p.read_text())
    if fault=='exit':d['code']=0
    elif fault=='error':d['error']=None
    elif fault=='reaped':d['reaped']=False
    elif fault in ['owner','group']:
     q=root/'child.json';a=json.loads(q.read_text());a['parent' if fault=='owner' else 'group']+=1;q.write_text(json.dumps(a))
    elif fault=='continued':d['second_hex']='ffffffff'
    elif fault=='stable':d['stable_hex']='00000000'
    else:d['child_done']=True
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='871b4baefb8b97fa95f3cc7f085a6dd7546a94dc7eb54f46dbfacdbd019f35d7'
