"""Discriminating actual owned Rust toolchain failure and recovery controls."""
import json,subprocess,shutil,sys
from pathlib import Path
from reloop.core import ROOT,PROJECT_ROOT,atomic,digest
from reloop.liveswapprobe import anchored

def corpus(out):
    out=Path(out);out.mkdir();prior=PROJECT_ROOT/'research/evidence/rust-source-2026-10-10'
    assert digest(prior/'manifest.json')=='7cf8a0b11b90f5f479e8409ba909a160ab77c738a88804b9ab5724ac0a631382'
    for name,row in json.loads((prior/'manifest.json').read_text())['files'].items():
        target=prior/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts and not target.is_symlink()
        assert target.stat().st_size==row['bytes'] and digest(target)==row['sha256']
    identity=json.loads((prior/'control/config.json').read_text());result=json.loads((prior/'control/live/result.json').read_text());stage=prior/'control/live'/result['builds'][0]['stage']/'result'
    import re
    shutil.copyfile(prior/'frozen/contract.rs',out/'contract.rs');generated=out/'kernel.rs'
    text=(stage/'module.rs').read_text();text=re.sub(r'#\[path = "[^"]+"\]', '#[path = "'+str(out/'contract.rs')+'"]',text);generated.write_text(text)
    assert digest(identity['rustc'])==identity['rustcSha'];helper=out.parent/'observed-compiler/owned-process-snapshot'
    config={'rustc':identity['rustc'],'rustcSha':identity['rustcSha'],'python':sys.executable,'source':str(prior/'fixture/0-source.swift'),'expected':str(prior/'fixture/0-expected.raw'),'module':str(stage/'view.wasm'),'generated':str(generated),'config':result['builds'][0]['receipt']['config'],'observer':{'helper':str(helper),'sha256':digest(helper)}};atomic(out/'config.json',config)
    r=subprocess.run([shutil.which('node'),str(ROOT/'tools/re/tests/rust_failure_control.js'),str(out/'config.json'),str(out/'controls')],capture_output=True,timeout=20);(out/'control.stdout').write_bytes(r.stdout);(out/'control.stderr').write_bytes(r.stderr);r.check_returncode();assert digest(identity['rustc'])==identity['rustcSha']
    d=json.loads((out/'controls/result.json').read_text());facts={'rust_failure_controls':len(d['controls']),'rust_failure_retained_bytes':len(d['controls'])*16384,'rust_failure_late_artifacts_stable':all(r['lateArtifactStable'] for r in d['controls']),'rust_failure_recovery_revision':d['recovery']['revision'],'rust_failure_zero_workers':d['finalStatus']['liveWorkers']==0}
    atomic(out/'result.json',{'observations':facts,'prior_anchor':'7cf8a0b11b90f5f479e8409ba909a160ab77c738a88804b9ab5724ac0a631382','scope':d['scope']});return facts
