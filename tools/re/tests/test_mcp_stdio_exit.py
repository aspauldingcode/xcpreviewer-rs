import base64,hashlib,importlib.util,json,shutil,tempfile,unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('exit_reader',Path(__file__).with_name('verify_mcp_stdio_exit.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class StdioExitTests(unittest.TestCase):
 def test_seal_and_current_entrypoint(self):
  e=ROOT/'research/evidence/mcp-stdio-exit-2026-10-11';self.assertEqual(reader.verify(e)['complete_bytes'],65536);self.assertEqual((ROOT/'tools/re/preview_mcp_stdio.js').read_bytes(),(e/'fixed/runtime/tools/re/preview_mcp_stdio.js').read_bytes())
 def test_current_actual_process_exit(self):
  with tempfile.TemporaryDirectory() as tmp:subprocess.run([__import__('sys').executable,str(ROOT/'tools/re/tests/mcp_stdio_exit_control.py'),str(ROOT),str(ROOT/'tools/re/tests/mcp_stdio_exit_preloader.js'),str(Path(tmp)/'out'),'fixed'],capture_output=True,check=True,timeout=12)
 def test_resealed_exit_cleanup_final_wire_bytes(self):
  for kind in ['wait','exit','cleanup','worker','stderr','padding','tail']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/mcp-stdio-exit-2026-10-11',e);p=e/'fixed/process/result.json';d=json.loads(p.read_text());row=d['records'][1]
    if kind=='wait':(e/'fixed/wait.json').write_text(json.dumps({'code':1,'stdout':'','stderr':'','timeout':False}))
    elif kind=='exit':row['code']=0
    elif kind=='cleanup':row['lifecycle']['channel']['cleanup']='complete'
    elif kind=='worker':row['lifecycle']['final']['lifecycle']['liveWorkers']=1
    elif kind=='stderr':(e/'fixed/process/failed/stderr.txt').write_text(json.dumps({'private':'secret'}))
    else:
     f=row['packets'][2]['result']['structuredContent']['frame'];b=bytearray(base64.b64decode(f['allocationBase64']));b[4 if kind=='padding' else 16383]^=1;f['allocationBase64']=base64.b64encode(b).decode();f['descriptor']['allocationSha256']=hashlib.sha256(b).hexdigest();status=json.loads(row['packets'][1]['result']['content'][0]['text']);status['frame']=f['descriptor'];row['packets'][1]['result']['content'][0]['text']=json.dumps(status)
    if kind in ['cleanup','worker']:(e/'fixed/process/failed/builds/session-lifecycle.json').write_text(json.dumps(row['lifecycle']))
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
