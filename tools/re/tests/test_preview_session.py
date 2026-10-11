import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('session_reader',Path(__file__).with_name('verify_preview_session.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class PreviewSessionTests(unittest.TestCase):
    def test_actual_compiler_consumer_and_independent_bytes(self):self.assertEqual(reader.verify(ROOT/'research/evidence/preview-session-2026-10-11')['consumer_controls'],8)
    def test_resealed_geometry_hidden_failure_and_padding(self):
        for kind in ['geometry','failure','padding']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/preview-session-2026-10-11',folder);p=folder/'session/result.json';d=json.loads(p.read_text())
                if kind=='geometry':d['states'][1]['frame']['width']=13
                elif kind=='failure':d['states'][2]['diagnostics']['lastFailure']['kind']='published'
                else:
                    p=folder/'session/retained.raw';b=bytearray(p.read_bytes());b[36]^=1;p.write_bytes(b)
                if kind!='padding':p.write_text(json.dumps(d))
                (folder/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}}))
                with self.assertRaises(AssertionError):reader.verify(folder)
