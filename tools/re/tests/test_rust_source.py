import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('source_reader',Path(__file__).with_name('verify_rust_source.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RustSourceTests(unittest.TestCase):
    def test_source_identity_drain_and_allocation_bytes(self):
        self.assertEqual(reader.verify(ROOT/'research/evidence/rust-source-2026-10-10')['bytes'],49152)
    def test_resealed_false_padding_compiler_and_drain(self):
        for kind in ['padding','compiler','drain']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/rust-source-2026-10-10',folder)
                if kind=='padding':p=folder/'control/live/0-frame.raw';b=bytearray(p.read_bytes());b[52]^=1;p.write_bytes(b)
                else:
                    p=folder/'control/live/result.json';d=json.loads(p.read_text())
                    if kind=='compiler':d['builds'][0]['receipt']['rustc_sha256']='0'*64
                    else:d['builds'][0]['execution']['report']['drained']=False
                    p.write_text(json.dumps(d))
                m=json.loads((folder/'manifest.json').read_text());m['files']={str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(AssertionError):reader.verify(folder)
