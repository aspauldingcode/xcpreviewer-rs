"""Actual Rust builder under source-file supersession and close boundaries."""
import json,subprocess,shutil
from pathlib import Path
from reloop.core import ROOT,atomic

def corpus(source,out):
    source=Path(source);out=Path(out);out.mkdir()
    r=subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/rust_file_controls.js'),str(source/'config.json'),str(out)],capture_output=True,timeout=20)
    (out/'control.stdout').write_bytes(r.stdout);(out/'control.stderr').write_bytes(r.stderr);r.check_returncode()
    d=json.loads((out/'result.json').read_text());facts={'rust_file_stale_rejected':d['stale']['rejected'],'rust_file_abort_drained':d['close']['drained'],'rust_file_controls_bytes':65536,'rust_file_controls_quiescent':all(not x['status']['building'] and x['status']['timers']==0 and x['status']['liveWorkers']==0 for x in [d['stale'],d['close']])}
    atomic(out/'observations.json',{'observations':facts,'scope':d['scope']});return facts
