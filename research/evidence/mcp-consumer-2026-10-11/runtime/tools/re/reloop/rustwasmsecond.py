"""Independent WasmKit execution of Rust modules and full-allocation checker controls."""
import json,subprocess,shutil
from pathlib import Path
from reloop.core import ROOT,atomic,digest
from reloop.portable import TOOLCHAIN
from reloop.rustframeprobe import RUSTC
from reloop.wasmkit import parse_result

def corpus(inputs,out):
    inputs=Path(inputs);out=Path(out);out.mkdir();runtime=TOOLCHAIN/'wasmkit'
    index=json.loads((inputs/'inputs/corpus.json').read_text());rows=[];abi=[];seen=set()
    def run(module,function,value=None):
        args=[str(runtime),'run',str(module),function]+([] if value is None else ['i32:'+str(value)])
        r=subprocess.run(args,capture_output=True,timeout=3);r.check_returncode();return parse_result(r.stdout.decode()),r.stdout.decode()
    records=index['records'][::2]; checker=(ROOT/'tools/re/rust/canvas-core/src/wasm-checker.rs').read_text();source_modules=json.loads((inputs/'result.json').read_text())['modules']
    for n,row in enumerate(records):
        module=inputs/'inputs'/row['module'];c=row['config']
        if row['module'] not in seen:
            cap,capraw=run(module,'capacity');pointer,ptrraw=run(module,'pixels');assert cap==16384 and 0<=pointer<=131072-16384
            abi.append({'module':row['module'],'capacity':cap,'pointer':pointer,'capacity_stdout':capraw,'pointer_stdout':ptrraw});seen.add(row['module'])
        rendered,raw=run(module,'render',row['stride']);assert rendered==row['stride']*c['height']
        original=next(x for x in source_modules if x['module']==row['module'])
        source=(inputs/original['generated']).read_text()
        extra=checker.replace('EXPECTED_PATH',str(inputs/'inputs'/row['expected'])).replace('STRIDE',str(row['stride'])).replace('HEIGHT',str(c['height'])).replace('PADDING',str(c['width']*4 if row['stride']>c['width']*4 else 0))
        generated=out/('checker-%d.rs'%n);generated.write_text(source+extra);target=out/('checker-%d.wasm'%n)
        args=[RUSTC,'--edition=2021','--target','wasm32-wasip1','--crate-type','cdylib','-C','panic=abort','-C','opt-level=2','-C','link-arg=--initial-memory=131072','-C','link-arg=--max-memory=131072','-C','link-arg=-zstack-size=8192',str(generated),'-o',str(target)]
        r=subprocess.run(args,capture_output=True,timeout=20);(out/('compile-%d.stderr'%n)).write_bytes(r.stderr);r.check_returncode()
        controls=[]
        for mutation in range(5):
            value,stdout=run(target,'verify',mutation);assert value==(1 if mutation in [1,2,3] else 0)
            controls.append({'mutation':mutation,'mismatches':value,'stdout':stdout})
        # Different engine runs exactly the same instrumented module and expected array.
        script="const f=require('fs'),e=new WebAssembly.Instance(new WebAssembly.Module(f.readFileSync(process.argv[1]))).exports;console.log(JSON.stringify([0,1,2,3,4].map(x=>e.verify(x))));"
        r=subprocess.run([shutil.which('node'),'-e',script,str(target)],capture_output=True,check=True,timeout=3);v8=json.loads(r.stdout);assert v8==[0,1,1,1,0]
        rows.append({'job':row['job'],'config':c,'stride':row['stride'],'expected':'../rust-wasm/inputs/'+row['expected'],'module':target.name,'module_sha256':digest(target),'render_stdout':raw,'rendered':rendered,'controls':controls,'v8':v8,'native':row['native'] is not None})
    facts={'rust_second_jobs':len(rows),'rust_second_controls':len(rows)*5,'rust_second_compared_bytes':len(rows)*5*16384,'rust_second_mutants':len(rows)*3,'rust_second_abi_modules':len(abi),'rust_second_all_equal':True}
    atomic(out/'result.json',{'observations':facts,'rows':rows,'abi':abi,'runtime_sha256':digest(runtime),'checker_source_sha256':digest(ROOT/'tools/re/rust/canvas-core/src/wasm-checker.rs'),'scope':'WasmKit and V8 on macOS; original Rust render receipts plus instrumented full-allocation comparator; no browser/non-Apple/native Canvas acceptance'})
    return facts
