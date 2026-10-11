import base64,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('sdk_reader',Path(__file__).with_name('verify_mcp_sdk.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class McpSdkTests(unittest.TestCase):
 def test_official_client_frames_and_owned_waits(self):self.assertEqual(reader.verify(ROOT/'research/evidence/mcp-sdk-2026-10-11')['complete_bytes'],81920)
 def test_resealed_sdk_version_wait_and_padding(self):
  for kind in ['version','wait','padding']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/mcp-sdk-2026-10-11',e);p=e/'process/result.json';d=json.loads(p.read_text())
    if kind=='version':d['sdkVersion']='0.0.0'
    elif kind=='wait':d['records'][1]['wait']['code']=1
    else:
     r=d['records'][0]['values'][3]['result'];f=json.loads(r['content'][0]['text']);b=bytearray(base64.b64decode(f['allocationBase64']));b[44]^=1;f['allocationBase64']=base64.b64encode(b).decode();r['content'][0]['text']=json.dumps(f)
     # Keep the transcript correlated; independent bytes must still reject.
     d['records'][0]['wire'][12]['message']['result']=r
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
