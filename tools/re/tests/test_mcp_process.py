import hashlib,importlib.util,json,shutil,tempfile,unittest,base64
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('mcp_process_reader',Path(__file__).with_name('verify_mcp_process.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class McpProcessTests(unittest.TestCase):
    def test_owned_process_frames_eof_and_fresh_oracle(self):self.assertEqual(reader.verify(ROOT/'research/evidence/mcp-process-2026-10-11')['fresh_modules'],3)
    def test_resealed_exit_eof_reply_and_packet_padding(self):
        for kind in ['exit','eof','cancel','padding']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/mcp-process-2026-10-11',folder);p=folder/'process/result.json';d=json.loads(p.read_text())
                if kind=='exit':d['records'][0]['code']=1
                elif kind=='eof':d['records'][1]['packets']=[{'id':1,'ok':True,'result':{}}]
                elif kind=='cancel':d['records'][3]['lifecycle']['failures'][0]['record']['report']['target_code']=0
                else:
                    content=d['records'][0]['packets'][5]['result']['content'][0];packet=json.loads(content['text']);b=bytearray(base64.b64decode(packet['allocationBase64']));b[44]^=1;packet['allocationBase64']=base64.b64encode(b).decode();content['text']=json.dumps(packet)
                p.write_text(json.dumps(d));(folder/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}}))
                with self.assertRaises(AssertionError):reader.verify(folder)
