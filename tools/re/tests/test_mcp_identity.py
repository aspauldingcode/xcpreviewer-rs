import subprocess,base64,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('identity_reader',Path(__file__).with_name('verify_mcp_identity.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class McpIdentityTests(unittest.TestCase):
 def test_old_acceptance_and_fixed_rejection(self):self.assertEqual(reader.verify(ROOT/'research/evidence/mcp-identity-2026-10-11')['complete_bytes'],131072)
 def test_current_helper_and_prior_controls(self):
  helper=ROOT/'tools/re/reloop/preview_consumer.js'
  for kind in ['consumer','terminal','identity']:
   e=ROOT/f'research/evidence/mcp-{kind}-2026-10-11';fixture=e/('process/result.json' if kind=='consumer' else 'fixture/result.json');p=subprocess.run([shutil.which('node'),str(e/f'control/preview_{kind}_control.js'),str(helper),str(fixture)],capture_output=True,timeout=3);self.assertEqual(p.returncode,0,p.stderr)
   result=json.loads(p.stdout);self.assertTrue(all(x['rejected'] for x in result['outcomes']))
 def test_resealed_result_padding_and_runtime_faults(self):
  for kind in ['verdict','padding','runtime','fixture']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(ROOT/'research/evidence/mcp-identity-2026-10-11',e)
    if kind in ['verdict','padding']:
     p=e/'result.json';d=json.loads(p.read_text())
     if kind=='verdict':d['outcomes'][0]['rejected']=False
     else:
      for x in d['outcomes']:
       b=bytearray(base64.b64decode(x['allocationBase64']));b[44]^=1;x['allocationBase64']=base64.b64encode(b).decode()
     p.write_text(json.dumps(d))
    elif kind=='runtime':shutil.copyfile(e/'baseline/preview_consumer.js',e/'runtime/preview_consumer.js')
    else:
     p=e/'fixture/result.json';d=json.loads(p.read_text());d['records'][0]['values'][22]['result']['content'][0]['text']='{}';p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
