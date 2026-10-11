"""Scoped frontend, frozen Rust compiler identity and live source revision controls."""
import json,subprocess,sys,shutil
from pathlib import Path
from reloop.core import ROOT,PROJECT_ROOT,atomic,digest
from reloop.liveswapprobe import anchored
from reloop.primarysource import parse,rejected_sources

def corpus(out):
    out=Path(out);out.mkdir();fixture=anchored('research/evidence/source-revision-2026-10-10','c53084d90de41c1e42cb8c17a38cf3b70e4fa0e6551a5937a4de7d536272e4ac')
    compiler=Path(subprocess.run(['/Users/8amps/.cargo/bin/rustup','which','rustc'],capture_output=True,check=True,timeout=3).stdout.decode().strip());assert compiler.is_absolute() and not compiler.is_symlink()
    helper=out.parent/'observed-compiler/owned-process-snapshot'
    config={'python':sys.executable,'cli':str(ROOT/'tools/re/rust_source_cli.py'),'rustc':str(compiler),'rustcSha':digest(compiler),'input':str(fixture),'observer':{'helper':str(helper),'sha256':digest(helper)}};atomic(out/'config.json',config)
    controls=[]
    for text in rejected_sources():
        try:parse(text)
        except ValueError as e:controls.append({'source':text,'error':str(e)})
        else:raise ValueError('Unsupported source accepted')
    atomic(out/'unsupported.json',controls)
    r=subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/rust_source_control.js'),str(out/'config.json'),str(out/'live')],capture_output=True,timeout=30);(out/'control.stdout').write_bytes(r.stdout);(out/'control.stderr').write_bytes(r.stderr);r.check_returncode()
    assert digest(compiler)==config['rustcSha'];d=json.loads((out/'live/result.json').read_text())
    facts={'rust_source_revisions':len(d['records']),'rust_source_bytes':len(d['records'])*16384,'rust_source_unsupported':len(controls),'rust_source_drained':all(x['execution']['report']['drained'] for x in d['builds']),'rust_source_failure_retained':len(d['failures'])==1 and d['failures'][0]['record']['report']['target_code']==2,'rust_source_zero_workers':d['finalStatus']['liveWorkers']==0}
    atomic(out/'result.json',{'observations':facts,'compiler_sha256':config['rustcSha'],'scope':d['scope']});return facts
