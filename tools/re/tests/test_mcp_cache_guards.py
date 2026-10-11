import hashlib,importlib.util,json,shutil,tempfile,unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('cache_reader',Path(__file__).with_name('verify_mcp_cache_guards.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class CacheGuardTests(unittest.TestCase):
 def test_sealed_histories_and_current_source(self):
  e=ROOT/'research/evidence/mcp-cache-guards-2026-10-11';self.assertEqual(reader.verify(e)['complete_bytes'],786432)
  for n in ['preview_consumer.js','preview_readiness.js','preview_frame_contract.js']:self.assertEqual((ROOT/'tools/re/reloop'/n).read_bytes(),(e/'runtime'/n).read_bytes())
 def test_current_replay(self):
  with tempfile.TemporaryDirectory() as tmp:subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/mcp_cache_guards_control.js'),str(ROOT/'tools/re/reloop/preview_consumer.js'),str(ROOT/'research/evidence/mcp-cache-guards-2026-10-11/fixture.json'),tmp],capture_output=True,check=True,timeout=5)
 def test_resealed_semantic_faults(self):
  for kind in ['wait','error','calls','revision','state','mutant','padding','tail']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/mcp-cache-guards-2026-10-11',e);p=e/'0/result.json';d=json.loads(p.read_text())
    if kind=='wait':(e/'0/wait.json').write_text(json.dumps({'code':1,'stdout':'','stderr':'','timeout':False}))
    elif kind=='error':d['rows'][0]['error']='different failure'
    elif kind=='calls':d['rows'][12]['calls'][1]='preview_frame'
    elif kind=='revision':d['rows'][13]['accepted']['revision']=1
    elif kind=='state':d['rows'][12]['accepted']['state']='ready'
    elif kind=='mutant':(e/'mutants/diagnostic/process/wait.json').write_text(json.dumps({'code':0,'stdout':'','stderr':'','timeout':False}))
    else:
     p1=e/'0/retry.raw';b=bytearray(p1.read_bytes());b[4 if kind=='padding' else 16383]^=1;p1.write_bytes(b)
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
