import hashlib,importlib.util,json,shutil,tempfile,unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('cleanup_reader',Path(__file__).with_name('verify_mcp_channel_cleanup.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class CleanupTests(unittest.TestCase):
 def test_seal_and_current_channel(self):
  e=ROOT/'research/evidence/mcp-channel-cleanup-2026-10-11';self.assertEqual(reader.verify(e)['complete_bytes'],262144);self.assertEqual((ROOT/'tools/re/reloop/mcp_channel.js').read_bytes(),(e/'fixed/runtime/mcp_channel.js').read_bytes())
 def test_current_owned_cleanup(self):
  with tempfile.TemporaryDirectory() as tmp:subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/mcp_channel_cleanup_control.js'),str(ROOT/'tools/re/reloop'),tmp,'fixed'],capture_output=True,check=True,timeout=5)
 def test_current_existing_channel_controls(self):
  p=subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/mcp_channel_control.js'),str(ROOT/'tools/re/reloop/preview_mcp.js'),str(ROOT/'tools/re/reloop/mcp_channel.js')],capture_output=True,check=True,timeout=5)
  d=json.loads(p.stdout);self.assertEqual(len(d['controls']),10)
  for x in d['controls']:self.assertEqual(x['result']['cleanup'],'complete');self.assertEqual(x['final'],{'closed':True,'pending':False})
 def test_resealed_cleanup_release_wait_and_bytes(self):
  for kind in ['wait','failed','complete','worker','timer','wire','padding','tail']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/mcp-channel-cleanup-2026-10-11',e);p=e/'fixed/0/result.json';d=json.loads(p.read_text())
    if kind=='wait':(e/'fixed/0/wait.json').write_text(json.dumps({'code':1,'stdout':'','stderr':'','timeout':False}))
    elif kind=='failed':d['rows'][1]['summary']['cleanup']='complete'
    elif kind=='complete':d['rows'][0]['summary']['cleanup']='failed'
    elif kind=='worker':d['rows'][1]['after']['lifecycle']['liveWorkers']=0
    elif kind=='timer':d['rows'][2]['after']['lifecycle']['timers']=2
    elif kind=='wire':d['rows'][1]['wire']='{"private":"secret"}'
    else:
     p1=e/'fixed/0/before-release/retained.raw';b=bytearray(p1.read_bytes());b[4 if kind=='padding' else 16383]^=1;p1.write_bytes(b)
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
