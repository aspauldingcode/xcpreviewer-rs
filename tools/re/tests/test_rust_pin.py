import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('pin_reader',Path(__file__).with_name('verify_rust_pin.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RustPinTests(unittest.TestCase):
    def test_identity_and_actual_reusable_builder_allocations(self):
        self.assertEqual(reader.verify(ROOT/'research/evidence/rust-toolchain-pin-2026-10-10')['bytes'],49152)
    def test_resealed_false_target_linker_and_identity_rejection(self):
        for kind in ['target','linker','missing','reject']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/rust-toolchain-pin-2026-10-10',folder)
                if kind=='reject':p=folder/'negative.json';d=json.loads(p.read_text());d['output_absent']=False;p.write_text(json.dumps(d))
                else:
                    from reloop.core import canonical_hash
                    p=folder/'control/toolchain.json';d=json.loads(p.read_text())
                    if kind=='missing':del d['identity']['target_files'][next(iter(d['identity']['target_files']))]
                    else:key=next(iter(d['identity']['target_files'])) if kind=='target' else 'rust-lld';d['identity']['target_files' if kind=='target' else 'linkers'][key]['sha256']='0'*64
                    d['sha256']=canonical_hash(d['identity']);p.write_text(json.dumps(d))
                    config=folder/'control/config.json';c=json.loads(config.read_text());c['toolchainPin']=d['sha256'];config.write_text(json.dumps(c))
                    receipt=folder/'control/live/result.json';r=json.loads(receipt.read_text())
                    for row in r['builds']:row['receipt']['toolchain_sha256']=d['sha256']
                    receipt.write_text(json.dumps(r))
                m=json.loads((folder/'manifest.json').read_text());m['files']={str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(AssertionError):reader.verify(folder)
