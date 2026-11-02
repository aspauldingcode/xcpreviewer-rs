"""Finite actual source-file build deadline, pin failure and postcompile validation failure."""
import json,subprocess,shutil
from pathlib import Path
from reloop.core import ROOT,atomic

def corpus(source,out):
    source=Path(source);out=Path(out);out.mkdir()
    r=subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/rust_file_failure.js'),str(source/'config.json'),str(out)],capture_output=True,timeout=25)
    (out/'control.stdout').write_bytes(r.stdout);(out/'control.stderr').write_bytes(r.stderr);r.check_returncode()
    d=json.loads((out/'result.json').read_text());facts={'rust_file_failure_cases':len(d['controls']),'rust_file_failure_bytes':len(d['controls'])*49152,'rust_postcompile_failure_recorded':d['controls'][2]['failure']['record']['report']['target_code']==0,'rust_file_timeout_recovered':d['controls'][0]['failure']['record']['report']['failure']=='deadline' and d['controls'][0]['recoveryRevision']==2}
    atomic(out/'observations.json',{'observations':facts,'scope':d['scope']});return facts
