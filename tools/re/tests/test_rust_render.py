import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('render_reader',Path(__file__).with_name('verify_rust_render.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RustRenderTests(unittest.TestCase):
    def test_every_rust_produced_byte_against_fraction_and_native(self):
        self.assertEqual(reader.verify(ROOT/'research/evidence/rust-primary-render-2026-10-10')['complete_bytes'],1376256)
    def test_resealed_false_pixel_tail_and_failure_claims(self):
        for kind in ['pixel','tail','failure']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/rust-primary-render-2026-10-10',folder)
                name='control/result.json' if kind=='failure' else 'control/frame-0.raw';p=folder/name
                if kind=='failure':d=json.loads(p.read_text());d['controls'][0]['unchanged']=False;p.write_text(json.dumps(d))
                else:data=bytearray(p.read_bytes());data[0 if kind=='pixel' else -1]^=1;p.write_bytes(data)
                m=json.loads((folder/'manifest.json').read_text());m['files'][name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(AssertionError):reader.verify(folder)
