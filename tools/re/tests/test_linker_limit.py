import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('linker_reader',Path(__file__).with_name('verify_linker_limit.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class LinkerLimitTests(unittest.TestCase):
    def test_retained_modules_and_missing_receipts(self):self.assertEqual(reader.verify(ROOT/'research/evidence/linker-observation-limit-2026-10-11')['bytes'],32768)
    def test_resealed_false_receipt_and_pixel(self):
        for kind in ['receipt','pixel']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/linker-observation-limit-2026-10-11',folder)
                if kind=='receipt':p=folder/'provenance.json';d=json.loads(p.read_text());d['attempt_reports_missing']=False;p.write_text(json.dumps(d))
                else:
                    p=folder/'attempts/0/linker/baseline.raw';b=bytearray(p.read_bytes());b[52]^=1;p.write_bytes(b)
                    q=folder/'attempts/0/manifest.json';d=json.loads(q.read_text());d['files']['linker/baseline.raw']={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};q.write_text(json.dumps(d))
                m=json.loads((folder/'manifest.json').read_text());m['files']={str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(AssertionError):reader.verify(folder)
