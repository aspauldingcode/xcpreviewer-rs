import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('diagnostic_reader',Path(__file__).with_name('verify_file_diagnostics.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class FileDiagnosticTests(unittest.TestCase):
    def test_bounded_owned_failures_and_fresh_replay(self):self.assertEqual(reader.verify(ROOT/'research/evidence/file-diagnostics-2026-10-11')['rejections'],80)
    def test_resealed_count_error_and_padding(self):
        for kind in ['count','error','padding']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/file-diagnostics-2026-10-11',folder);p=folder/'control/result.json';d=json.loads(p.read_text())
                if kind=='count':d['diagnostics']['droppedEvents']=0
                elif kind=='error':d['events'][1]['error']='🔥'*200
                else:
                    p=folder/'control/retained.raw';b=bytearray(p.read_bytes());b[52]^=1;p.write_bytes(b)
                if kind!='padding':p.write_text(json.dumps(d))
                (folder/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}}))
                with self.assertRaises(AssertionError):reader.verify(folder)
