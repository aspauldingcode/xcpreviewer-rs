import hashlib,importlib.util,json,shutil,tempfile,unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('cap_reader',Path(__file__).with_name('verify_mcp_request_cap.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RequestCapTests(unittest.TestCase):
 def test_seal_and_fixed_source(self):
  e=ROOT/'research/evidence/mcp-request-cap-2026-10-11';self.assertEqual(reader.verify(e)['complete_bytes'],98304);self.assertEqual((ROOT/'tools/re/reloop/preview_mcp.js').read_bytes(),(e/'fixed/runtime/preview_mcp.js').read_bytes())
 def test_current_owned_cap(self):
  with tempfile.TemporaryDirectory() as tmp:subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/mcp_request_cap_control.js'),str(ROOT/'tools/re/reloop'),tmp,'fixed'],capture_output=True,check=True,timeout=5)
 def test_resealed_wait_release_limit_failure_bytes(self):
  for kind in ['wait','worker','timers','ids','response','cleanup','padding','tail']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/mcp-request-cap-2026-10-11',e);p=e/'fixed/0/result.json';d=json.loads(p.read_text())
    if kind=='wait':(e/'fixed/0/wait.json').write_text(json.dumps({'code':1,'stdout':'','stderr':'','timeout':False}))
    elif kind=='worker':d['after']['lifecycle']['liveWorkers']=1
    elif kind=='timers':d['after']['lifecycle']['timers']=2
    elif kind=='ids':d['ids']=257
    elif kind=='response':d['limited']['error']['code']=0
    elif kind=='cleanup':d['cleanupFailure']['error']['message']='private cleanup secret'
    else:
     p1=e/'fixed/0/published.raw';b=bytearray(p1.read_bytes());b[4 if kind=='padding' else 16383]^=1;p1.write_bytes(b)
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
