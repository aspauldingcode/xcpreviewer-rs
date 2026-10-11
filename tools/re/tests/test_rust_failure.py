import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('failure_reader',Path(__file__).with_name('verify_rust_failure.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RustFailureTests(unittest.TestCase):
    def test_actual_compiler_failure_frames_and_recovery(self):
        self.assertEqual(reader.verify(ROOT/'research/evidence/rust-failure-2026-10-10')['retained_bytes'],49152)
    def test_resealed_false_wait_status_late_artifact_and_padding(self):
        for kind in ['wait','late','padding']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/rust-failure-2026-10-10',folder)
                if kind=='padding':p=folder/'control/controls/abort-retained.raw';b=bytearray(p.read_bytes());b[52]^=1;p.write_bytes(b)
                else:
                    p=folder/'control/controls/result.json';d=json.loads(p.read_text())
                    if kind=='wait':d['controls'][0]['execution']['report']['target_code']=0
                    else:d['controls'][0]['lateArtifactStable']=False
                    p.write_text(json.dumps(d))
                m=json.loads((folder/'manifest.json').read_text());m['files']={str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(AssertionError):reader.verify(folder)
