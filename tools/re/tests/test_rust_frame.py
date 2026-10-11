import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('rust_reader',Path(__file__).with_name('verify_rust_frame.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RustFrameTests(unittest.TestCase):
    def test_controller_freezes_rust_implementation(self):
        from reloop.core import source_files
        self.assertTrue(any(p.name=="lib.rs" for p in source_files()))
    def test_frozen_full_allocations_and_rejection_receipts(self):
        self.assertEqual(reader.verify(ROOT/'research/evidence/rust-frame-core-2026-10-10')['compared_bytes'],1376256)
    def test_resealed_false_padding_and_acceptance_claims(self):
        for kind in ['padding','accept','error']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/rust-frame-core-2026-10-10',folder)
                name='control/padding.raw' if kind=='padding' else 'control/result.json';p=folder/name
                if kind=='padding':data=bytearray(p.read_bytes());data[-1]^=1;p.write_bytes(data)
                else:
                    d=json.loads(p.read_text())
                    if kind=='accept':d['rows'][0]['code']=2
                    else:d['controls'][0]['error']='rejected Length\n'
                    p.write_text(json.dumps(d))
                m=json.loads((folder/'manifest.json').read_text());m['files'][name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(AssertionError):reader.verify(folder)
