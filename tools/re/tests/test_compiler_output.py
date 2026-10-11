import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from reloop import sourcecache
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('compiler_output_reader',Path(__file__).with_name('verify_compiler_output.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class CompilerOutputTests(unittest.TestCase):
 def test_sealed_child_caps_and_current_builder(self):
  e=ROOT/'research/evidence/compiler-output-2026-10-11';self.assertEqual(hashlib.sha256((e/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertEqual(reader.verify(e)['complete_diagnostic_bytes'],24576);self.assertEqual((ROOT/'tools/re/reloop/sourcecache.py').read_bytes(),(e/'fixed-sourcecache.py').read_bytes())
 def test_bad_limit_before_launch(self):
  for value in [0,-1,True,1.5]:
   with self.subTest(value=value),patch.object(sourcecache.subprocess,'run') as run:
    with self.assertRaises(ValueError):sourcecache.run_compiler(['owned'],output_limit=value)
    run.assert_not_called()
 def test_resealed_false_acceptance(self):
  for fault in ['exit','timeout','reaped','parent','child','output','error']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/compiler-output-2026-10-11',e);root=e/'fixed/stdout';p=root/'wait.json';d=json.loads(p.read_text())
    if fault=='exit':d['code']=0
    elif fault=='timeout':d['timeout']=True
    elif fault=='reaped':d['reaped']=False
    elif fault=='parent':d['parent_limit_after']=[4096,4096]
    elif fault=='child':(root/'child.json').write_text(json.dumps({'file_limit':[9223372036854775807,9223372036854775807]}))
    elif fault=='output':d['stdout']='00'+d['stdout'][2:]
    else:d['error']=None
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)

SEAL='2e8b6a792a80ec21e379eb150c124e9e5d386251a55108e518185b0e66d8029b'
