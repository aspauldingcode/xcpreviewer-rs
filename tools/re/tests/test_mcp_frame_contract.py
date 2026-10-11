import base64,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('frame_reader',Path(__file__).with_name('verify_mcp_frame_contract.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class McpFrameContractTests(unittest.TestCase):
 def test_typed_frame_availability_sdk_and_full_bytes(self):self.assertEqual(reader.verify(ROOT/'research/evidence/mcp-frame-contract-2026-10-11')['complete_bytes'],81920)
 def test_resealed_availability_wait_and_padding(self):
  for kind in ['availability','wait','padding']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/mcp-frame-contract-2026-10-11',e);p=e/'process/result.json';d=json.loads(p.read_text())
    if kind=='wait':d['records'][1]['wait']['code']=1
    else:
     r=d['records'][0]['values'][2]['result'];f=r['structuredContent']
     if kind=='availability':f['available']=False;r['content'][0]['text']='No frame available.'
     else:
      b=bytearray(base64.b64decode(f['frame']['allocationBase64']));b[52]^=1;f['frame']['allocationBase64']=base64.b64encode(b).decode()
     d['records'][0]['wire'][10]['message']['result']=r
    p.write_text(json.dumps(d));(e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(e)
