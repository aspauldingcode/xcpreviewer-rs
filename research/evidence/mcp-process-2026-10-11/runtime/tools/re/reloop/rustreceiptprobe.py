"""Strict receipt gate against fresh actual finite Rust build receipts."""
import json,subprocess,shutil
from pathlib import Path
from reloop.core import ROOT,atomic

def corpus(source,out):
    source=Path(source);out=Path(out);out.mkdir()
    r=subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/rust_receipt_control.js'),str(source/'live/result.json'),str(out)],capture_output=True,timeout=5);(out/'control.stdout').write_bytes(r.stdout);(out/'control.stderr').write_bytes(r.stderr);r.check_returncode();d=json.loads((out/'result.json').read_text());facts={'rust_receipt_valid':len(d['valid']),'rust_receipt_mutants':len(d['mutants'])};atomic(out/'observations.json',{'observations':facts,'scope':'Strict receipt metadata and byte pins; not independent Swift lowering or native Canvas protocol'});return facts
