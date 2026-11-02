"""Owned filesystem controls for the actual Rust builder artifact reader."""
import json,subprocess,shutil,sys
from pathlib import Path
from reloop.core import ROOT,atomic

def corpus(source,out):
    source=Path(source);out=Path(out);out.mkdir();r=json.loads((source/'live/result.json').read_text());module=source/'live'/r['builds'][0]['stage']/'result/view.wasm'
    config={'module':str(module),'helper':str(ROOT/'tools/re/reloop/bounded_artifact.js'),'python':sys.executable};atomic(out/'config.json',config)
    r=subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/artifact_control.js'),str(out/'config.json'),str(out/'controls')],capture_output=True,timeout=20)
    (out/'control.stdout').write_bytes(r.stdout);(out/'control.stderr').write_bytes(r.stderr);r.check_returncode();d=json.loads((out/'controls/result.json').read_text())
    facts={'artifact_read_cases':len(d['controls']),'artifact_read_descriptors_closed':all(x['opened']==x['closed'] for x in d['controls']),'artifact_read_bounded':all(x['elapsedMs']<2000 for x in d['controls'])}
    atomic(out/'observations.json',{'observations':facts,'scope':d['scope']});return facts
