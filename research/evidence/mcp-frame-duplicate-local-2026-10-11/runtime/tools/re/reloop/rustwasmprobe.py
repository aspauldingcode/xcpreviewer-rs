"""Owned no_std Rust WASM modules, tested against independent pinned allocations."""
import json, shutil, subprocess
from pathlib import Path
from reloop.core import ROOT, PROJECT_ROOT, atomic, digest
from reloop.livecorpus import prepare
from reloop.rustframeprobe import RUSTC

def corpus(out):
    out=Path(out); out.mkdir(); source=ROOT/'tools/re/rust/canvas-core/src'
    index=prepare(PROJECT_ROOT/'research/runs',out/'inputs'); compiled={}; modules=[]
    template=(source/'wasm-template.rs').read_text()
    for row in index['records']:
        c=row['config']; key=(c['width'],c['height'],*c['alphas'],c['reverse'])
        if key not in compiled:
            n=len(compiled); generated=out/('module-%d.rs'%n); target=out/('module-%d.wasm'%n)
            text=template.replace('CONTRACT_PATH',str(source/'contract.rs'))
            values=dict(zip(['WIDTH','HEIGHT','RED','GREEN','BLUE','REVERSE'],key))
            values['REVERSE']='true' if c['reverse'] else 'false'
            for name,value in values.items(): text=text.replace(name,str(value))
            generated.write_text(text)
            args=[RUSTC,'--edition=2021','--target','wasm32-wasip1','--crate-type','cdylib','-C','panic=abort','-C','opt-level=2','-C','link-arg=--initial-memory=131072','-C','link-arg=--max-memory=131072','-C','link-arg=-zstack-size=8192',str(generated),'-o',str(target)]
            r=subprocess.run(args,capture_output=True,timeout=20)
            (out/('compile-%d.stderr'%n)).write_bytes(r.stderr); r.check_returncode()
            name=digest(target)+'.wasm'; shutil.copyfile(target,out/'inputs'/name); compiled[key]=name
            modules.append({'config':c,'module':name,'generated':generated.name,'generated_sha256':digest(generated)})
        row['module']=compiled[key]
    index['scope']='Owned no_std Rust configuration modules in macOS V8; pinned public native/Fraction allocation controls; no Swift compiler, browser/Linux/Windows or native Canvas protocol acceptance'
    atomic(out/'inputs/corpus.json',index)
    r=subprocess.run([shutil.which('node'),str(ROOT/'tools/re/reloop/live_wasm_corpus.js'),str(out/'inputs'),str(out/'runtime')],capture_output=True,timeout=30)
    (out/'runtime.stdout').write_bytes(r.stdout); (out/'runtime.stderr').write_bytes(r.stderr); r.check_returncode()
    result=json.loads((out/'runtime/result.json').read_text())
    facts={'rust_wasm_frames':len(result['records']),'rust_wasm_bytes':sum(x['live_bytes'] for x in result['records']),'rust_wasm_native_bytes':sum(x['native_bytes'] for x in result['records']),'rust_wasm_faults':len(result['faults']),'rust_wasm_zero_workers':result['final_status']['liveWorkers']==0,'rust_wasm_modules':len(modules)}
    version=subprocess.run([RUSTC,'--version'],capture_output=True,check=True,timeout=2).stdout.decode().strip()
    atomic(out/'result.json',{'observations':facts,'compiler':version,'target':'wasm32-wasip1','modules':modules,'sources':{name:digest(source/name) for name in ['contract.rs','wasm-template.rs']},'scope':index['scope']})
    return facts
