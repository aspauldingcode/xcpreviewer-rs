import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('wasm_reader',Path(__file__).with_name('verify_rust_wasm.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RustWasmTests(unittest.TestCase):
    def test_every_byte_and_actual_abi(self):
        self.assertEqual(reader.verify(ROOT/'research/evidence/rust-wasm-2026-10-10')['invalid_strides'],336)
    def test_resealed_false_padding_abi_and_cleanup(self):
        for kind in ['padding','abi','cleanup']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/rust-wasm-2026-10-10',folder)
                name={'padding':'control/runtime/revision-6.raw','cleanup':'control/runtime/result.json','abi':'control/inputs/corpus.json'}[kind];p=folder/name
                if kind=='padding':b=bytearray(p.read_bytes());b[52]^=1;p.write_bytes(b)
                else:
                    d=json.loads(p.read_text())
                    if kind=='cleanup':d['final_status']['liveWorkers']=1
                    else:
                        old=d['records'][0]['module'];b=(folder/'control/inputs'/old).read_bytes();assert b'capacity' in b
                        b=b.replace(b'capacity',b'capacitX',1);sha=hashlib.sha256(b).hexdigest();name2=sha+'.wasm';(folder/'control/inputs'/name2).write_bytes(b);d['records'][0]['module']=name2
                        receipt=folder/'control/runtime/result.json';r=json.loads(receipt.read_text());r['records'][0]['module_sha256']=sha;receipt.write_text(json.dumps(r))
                    p.write_text(json.dumps(d))
                m=json.loads((folder/'manifest.json').read_text());m['files']={str(q.relative_to(folder)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in folder.rglob('*') if q.is_file() and q.name!='manifest.json'};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(AssertionError):reader.verify(folder)
