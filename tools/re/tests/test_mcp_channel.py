import importlib.util,json,hashlib,shutil,tempfile,unittest,base64
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('mcp_channel_reader',Path(__file__).with_name('verify_mcp_channel.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class McpChannelTests(unittest.TestCase):
 def test_bounded_stream_controls(self):self.assertEqual(reader.verify(ROOT/'research/evidence/mcp-channel-2026-10-11')['controls'],10)
 def test_resealed_suppression_cleanup_and_allocation(self):
  for kind in ['suppression','cleanup','allocation']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/mcp-channel-2026-10-11',folder);p=folder/'result.json';d=json.loads(p.read_text());c=d['observed']['controls']
    if kind=='suppression':c[1]['result']['suppressed']=0
    elif kind=='cleanup':c[2]['final']['pending']=True
    else:
     packet=c[0]['packets'][2]['result']['content'][0];f=json.loads(packet['text']);b=bytearray(base64.b64decode(f['allocationBase64']));b[44]^=1;f['allocationBase64']=base64.b64encode(b).decode();packet['text']=json.dumps(f)
    p.write_text(json.dumps(d));(folder/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}}))
    with self.assertRaises(AssertionError):reader.verify(folder)
