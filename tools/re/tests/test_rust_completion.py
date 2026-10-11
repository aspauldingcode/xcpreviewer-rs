import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('completion_reader',Path(__file__).with_name('verify_rust_completion.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RustCompletionTests(unittest.TestCase):
    def test_actual_completion_publication_veto(self):self.assertEqual(reader.verify(ROOT/'research/evidence/rust-completion-2026-10-11')['fresh_modules'],5)
    def test_resealed_publication_wait_and_padding_claims(self):
        for kind in ['publication','wait','padding']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/rust-completion-2026-10-11',folder)
                p=folder/'completion/result.json';d=json.loads(p.read_text())
                if kind=='publication':d['controls'][0]['events'].append({'kind':'published','generation':2,'revision':2})
                elif kind=='wait':d['controls'][0]['builds'][1]['execution']['report']['target_code']=-15
                else:
                    p=folder/'completion/supersede/final.raw';b=bytearray(p.read_bytes());b[52]^=1;p.write_bytes(b)
                if kind!='padding':p.write_text(json.dumps(d))
                m={'files':{str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(AssertionError):reader.verify(folder)
