import hashlib,importlib.util,json,shutil,tempfile,unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('live_reader',Path(__file__).with_name('verify_live_read_timeout.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class LiveReadTests(unittest.TestCase):
 def test_retained_baseline_and_fixed_quiescence(self):
  e=ROOT/'research/evidence/live-read-timeout-2026-10-11';self.assertEqual((ROOT/'tools/re/reloop/live_wasm_host.js').read_bytes(),(e/'fixed/live_wasm_host.js').read_bytes());self.assertEqual(reader.verify(e)['complete_bytes'],196608)
 def test_current_timeout_and_recovery(self):
  with tempfile.TemporaryDirectory() as tmp:
   subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/live_read_timeout_control.js'),str(ROOT/'tools/re/reloop/live_wasm_host.js'),tmp,'fixed'],capture_output=True,check=True,timeout=6)
 def test_resealed_worker_wait_recovery_close_bytes(self):
  for kind in ['wait','worker','repeat','revision','close','padding','tail']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/live-read-timeout-2026-10-11',e);root=e/'fixed/0';p=root/'result.json';d=json.loads(p.read_text())
    if kind=='wait':(root/'wait.json').write_text(json.dumps({'code':1,'stderr':'','stdout':'','timeout':False}))
    elif kind=='worker':d['rows'][0]['liveWorkers']=1
    elif kind=='repeat':d['second_error']='deadline'
    elif kind=='revision':d['rows'][2]['revision']=1
    elif kind=='close':d['final']['busy']=True
    else:
     b=bytearray((root/'retained.raw').read_bytes());b[4 if kind=='padding' else 16383]^=1;(root/'retained.raw').write_bytes(b)
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
