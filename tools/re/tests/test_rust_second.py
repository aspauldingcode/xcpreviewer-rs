import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('second_reader',Path(__file__).with_name('verify_rust_second.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RustSecondTests(unittest.TestCase):
    def test_independent_runtime_and_every_checker_byte(self):
        self.assertEqual(reader.verify(ROOT/'research/evidence/rust-second-runtime-2026-10-10')['controls'],210)
    def test_resealed_false_result_native_and_checker(self):
        for kind in ['result','native','checker']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/rust-second-runtime-2026-10-10',folder)
                d=json.loads((folder/'control/result.json').read_text())
                if kind=='result':d['rows'][0]['controls'][1]['mismatches']=0;(folder/'control/result.json').write_text(json.dumps(d))
                elif kind=='native':idx=json.loads((folder/'rust-wasm/inputs/corpus.json').read_text());p=folder/'rust-wasm/inputs'/idx['records'][0]['native'];b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b)
                else:p=folder/'control'/d['rows'][0]['module'];p.write_bytes(b'\0asm\1\0\0\0');d['rows'][0]['module_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();(folder/'control/result.json').write_text(json.dumps(d))
                m=json.loads((folder/'manifest.json').read_text());m['files']={str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises((AssertionError,ValueError)):reader.verify(folder)
