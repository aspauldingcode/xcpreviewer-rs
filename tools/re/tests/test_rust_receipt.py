import hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('receipt_reader',Path(__file__).with_name('verify_rust_receipt.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader)
class RustReceiptTests(unittest.TestCase):
    def test_actual_receipts_and_frozen_fault_replay(self):self.assertEqual(reader.verify(ROOT/'research/evidence/rust-receipt-2026-10-11')['mutants'],34)
    def test_resealed_false_validity_context_and_reverse_type(self):
        for kind in ['validity','context','reverse']:
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)/'evidence';shutil.copytree(ROOT/'research/evidence/rust-receipt-2026-10-11',folder);p=folder/'gate/result.json';d=json.loads(p.read_text())
                if kind=='validity':d['mutants'][0]['receipt']=d['valid'][0]['receipt']
                elif kind=='context':d['valid'][0]['context']['generated_sha256']='0'*64
                else:d['valid'][0]['receipt']['config']['reverse']=False
                p.write_text(json.dumps(d));m=json.loads((folder/'manifest.json').read_text());m['files']={str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'};(folder/'manifest.json').write_text(json.dumps(m))
                with self.assertRaises(AssertionError):reader.verify(folder)
