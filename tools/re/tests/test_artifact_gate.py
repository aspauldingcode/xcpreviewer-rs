import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('artifact_reader',Path(__file__).with_name('verify_artifact_gate.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class ArtifactGateTests(unittest.TestCase):
    def test_fresh_filesystem_replay(self):self.assertEqual(reader.verify(ROOT/'research/evidence/artifact-read-2026-10-11')['replayed'],8)
    def test_resealed_false_acceptance_descriptor_and_bytes(self):
        for kind in ['accept','descriptor','bytes']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/artifact-read-2026-10-11',folder);p=folder/'gate/result.json';d=json.loads(p.read_text())
                if kind=='accept':d['controls'][4]['accepted']=True
                elif kind=='descriptor':d['controls'][6]['closed']=0
                else:d['controls'][0]['sha']='0'*64
                p.write_text(json.dumps(d));m=json.loads((folder/'manifest.json').read_text());m['files']={str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(AssertionError):reader.verify(folder)
