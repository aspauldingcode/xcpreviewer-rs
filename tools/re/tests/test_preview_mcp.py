import importlib.util,json,hashlib,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('mcp_reader',Path(__file__).with_name('verify_preview_mcp.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class PreviewMcpTests(unittest.TestCase):
 def test_protocol_and_independent_replay(self):self.assertEqual(reader.verify(ROOT/'research/evidence/preview-mcp-handler-2026-10-11')['allocation_bytes'],32768)
 def test_resealed_claims_reject(self):
  for kind in ['version','leak','padding']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/preview-mcp-handler-2026-10-11',folder);p=folder/'result.json';d=json.loads(p.read_text())
    if kind=='version':d['observed']['packets'][1]['result']['protocolVersion']='unnegotiated'
    elif kind=='leak':d['observed']['packets'][7]['result']['content'][0]['text']='private secret'
    else:
     import base64
     packet=d['observed']['packets'][8]['result']['content'][0];f=json.loads(packet['text']);b=bytearray(base64.b64decode(f['allocationBase64']));b[44]^=1;f['allocationBase64']=base64.b64encode(b).decode();packet['text']=json.dumps(f)
    p.write_text(json.dumps(d));(folder/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(folder)
