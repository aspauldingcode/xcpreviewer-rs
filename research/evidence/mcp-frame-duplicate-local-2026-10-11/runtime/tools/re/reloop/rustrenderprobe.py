"""Independent Rust primary rendering against pinned native/Fraction full allocations."""
import subprocess,json
from pathlib import Path
from reloop.core import ROOT,PROJECT_ROOT,atomic,digest
from reloop.livecorpus import prepare
from reloop.rustframeprobe import RUSTC

def corpus(out):
    out=Path(out);out.mkdir();source=ROOT/'tools/re/rust/canvas-core/src';lib=out/'libcanvas_core.rlib';binary=out/'primary-render'
    for i,args in enumerate([[RUSTC,'--edition=2021','--crate-name','canvas_core','--crate-type','rlib',str(source/'lib.rs'),'-o',str(lib)],
                             [RUSTC,'--edition=2021',str(source/'bin/primary-render.rs'),'--extern','canvas_core='+str(lib),'-o',str(binary)]]):
        r=subprocess.run(args,capture_output=True,timeout=20);(out/('compile-%d.stdout'%i)).write_bytes(r.stdout);(out/('compile-%d.stderr'%i)).write_bytes(r.stderr);r.check_returncode()
    index=prepare(PROJECT_ROOT/'research/runs',out/'inputs');rows=[]
    for n,row in enumerate(index['records']):
        c=row['config'];args=[c['width'],c['height'],row['stride'],*c['alphas'],c['reverse']];target=out/('frame-%d.raw'%n)
        r=subprocess.run([str(binary),*map(str,args),str(target)],capture_output=True,timeout=2)
        assert r.returncode==0 and r.stdout==('rendered %d 16384\n'%(row['stride']*c['height'])).encode()
        actual=target.read_bytes();prediction=(out/'inputs'/row['expected']).read_bytes();assert len(actual)==16384 and actual==prediction
        if row['native']:assert actual==(out/'inputs'/row['native']).read_bytes()
        rows.append({'index':n,'args':args,'actual':target.name,'expected':'inputs/'+row['expected'],'code':r.returncode,'stdout':r.stdout.decode(),'sha256':digest(target),'native_bytes':16384 if row['native'] else 0})
    controls=[];base=[13,7,64,4,4,4,0]
    for kind,slot,value,error in [('width',0,0,'Dimensions'),('height',1,65,'Dimensions'),('stride',2,51,'Stride'),('alpha',3,9,'Alpha'),('order',6,2,'Unsupported primary order')]:
        args=base.copy();args[slot]=value;target=out/(kind+'-sentinel.raw');target.write_bytes(b'owned-output-sentinel')
        r=subprocess.run([str(binary),*map(str,args),str(target)],capture_output=True,timeout=2)
        assert r.returncode==2 and error.encode() in r.stderr and target.read_bytes()==b'owned-output-sentinel'
        controls.append({'kind':kind,'args':args,'code':r.returncode,'error':r.stderr.decode(),'target':target.name,'unchanged':True})
    facts={'rust_render_frames':len(rows),'rust_render_bytes':len(rows)*16384,'rust_render_native_bytes':sum(r['native_bytes'] for r in rows),'rust_render_invalid_controls':len(controls),'rust_render_invalid_unchanged':all(r['unchanged'] for r in controls),'scope':'Three-primary alpha-eighth configuration rendering only; no Swift parser, WASM executor, native Canvas wire or platform acceptance'}
    atomic(out/'result.json',{'observations':facts,'rows':rows,'controls':controls,'binary_sha256':digest(binary),'sources':{str(p.relative_to(source)):digest(p) for p in source.rglob('*.rs')}})
    return facts
