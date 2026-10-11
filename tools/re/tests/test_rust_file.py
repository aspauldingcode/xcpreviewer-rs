import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('file_reader',Path(__file__).with_name('verify_rust_file.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RustFileTests(unittest.TestCase):
    def test_actual_file_controls(self):self.assertEqual(reader.verify(ROOT/'research/evidence/rust-file-loop-2026-10-10')['bytes'],65536)
    def test_resealed_false_generation_drain_and_padding(self):
        for mode in ['generation','drain','padding']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/rust-file-loop-2026-10-10',folder)
                p=folder/'loops/result.json';d=json.loads(p.read_text())
                if mode=='generation':next(x for x in d['stale']['events'] if x['kind']=='rejected')['generation']=999
                elif mode=='drain':d['close']['failures'][0]['record']['report']['remaining_observed']=1
                else:
                    p=folder/'loops/close/final.raw';b=bytearray(p.read_bytes());b[52]^=1;p.write_bytes(b);d['close']['finalSha']=hashlib.sha256(b).hexdigest()
                (folder/'loops/result.json').write_text(json.dumps(d));m=json.loads((folder/'manifest.json').read_text());m['files']={str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(AssertionError):reader.verify(folder)
