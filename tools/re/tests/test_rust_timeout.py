import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('timeout_reader',Path(__file__).with_name('verify_rust_timeout.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RustTimeoutTests(unittest.TestCase):
    def test_actual_failures_and_recovery(self):self.assertEqual(reader.verify(ROOT/'research/evidence/rust-file-failure-2026-10-11')['bytes'],147456)
    def test_resealed_false_wait_recovery_and_padding(self):
        for mode in ['wait','recovery','padding']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/rust-file-failure-2026-10-11',folder);p=folder/'failures/result.json';d=json.loads(p.read_text())
                if mode=='wait':d['controls'][0]['failure']['record']['report']['target_code']=0
                elif mode=='recovery':d['controls'][1]['recoveryRevision']=99
                else:
                    p=folder/'failures/oracle/retained.raw';b=bytearray(p.read_bytes());b[52]^=1;p.write_bytes(b);d['controls'][2]['retainedSha']=hashlib.sha256(b).hexdigest()
                (folder/'failures/result.json').write_text(json.dumps(d));m=json.loads((folder/'manifest.json').read_text());m['files']={str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(AssertionError):reader.verify(folder)
