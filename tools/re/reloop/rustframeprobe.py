"""Frozen dependency-free Rust frame gate; owned portable policy, not native protocol."""
import json,subprocess,hashlib
from pathlib import Path
from reloop.core import ROOT,PROJECT_ROOT,atomic,digest
from reloop.livecorpus import prepare
RUSTC='/Users/8amps/.cargo/bin/rustc'

def corpus(out):
    out=Path(out);out.mkdir()
    source=ROOT/'tools/re/rust/canvas-core/src'
    identity=subprocess.run([RUSTC,'-vV'],check=True,capture_output=True,timeout=5).stdout.decode()
    lib=out/'libcanvas_core.rlib';binary=out/'frame-gate';tests=out/'core-tests'
    commands=[[RUSTC,'--edition=2021','--crate-name','canvas_core','--crate-type','rlib',str(source/'lib.rs'),'-o',str(lib)],
              [RUSTC,'--edition=2021',str(source/'main.rs'),'--extern','canvas_core='+str(lib),'-o',str(binary)],
              [RUSTC,'--edition=2021','--test',str(source/'lib.rs'),'-o',str(tests)]]
    for i,cmd in enumerate(commands):
        r=subprocess.run(cmd,capture_output=True,timeout=20);(out/('compile-%d.stdout'%i)).write_bytes(r.stdout);(out/('compile-%d.stderr'%i)).write_bytes(r.stderr);r.check_returncode()
    r=subprocess.run([str(tests)],capture_output=True,timeout=10);(out/'tests.stdout').write_bytes(r.stdout);(out/'tests.stderr').write_bytes(r.stderr);r.check_returncode()
    index=prepare(PROJECT_ROOT/'research/runs',out/'inputs');rows=[]
    for n,row in enumerate(index['records']):
        c=row['config'];args=[c['width'],c['height'],row['stride'],131072,131072-16384,16384,row['stride']*c['height']]
        prediction=out/'inputs'/row['expected'];actual=out/'inputs'/(row['native'] or row['expected'])
        r=subprocess.run([str(binary),*map(str,args),str(actual),str(prediction)],capture_output=True,timeout=2)
        assert r.returncode==0 and r.stdout==b'accepted 16384\n'
        rows.append({'index':n,'args':args,'actual':str(actual.relative_to(out)),'expected':str(prediction.relative_to(out)),'code':r.returncode,'stdout':r.stdout.decode(),'native_bytes':16384 if row['native'] else 0})
    controls=[];row=index['records'][6];assert row['config']['width']==13 and row['stride']==64
    expected=out/'inputs'/row['expected'];good=expected.read_bytes();base=[13,7,64,131072,114688,16384,448]
    for kind,offset in [('pixel',0),('padding',52),('tail',16383)]:
        bad=bytearray(good);bad[offset]^=1;p=out/(kind+'.raw');p.write_bytes(bad)
        r=subprocess.run([str(binary),*map(str,base),str(p),str(expected)],capture_output=True,timeout=2)
        assert r.returncode==2 and ('Mismatch(%d)'%offset).encode() in r.stderr
        controls.append({'kind':kind,'offset':offset,'args':base,'code':r.returncode,'error':r.stderr.decode(),'actual':p.name,'expected':str(expected.relative_to(out))})
    for kind,slot,value,error in [('overflow',4,18446744073709551615,'Span'),('span',4,114689,'Span'),('count',6,447,'Rendered'),('capacity',5,16383,'Capacity'),('memory',3,131073,'Memory'),('width',0,65,'Dimensions'),('stride',2,51,'Stride')]:
        args=base.copy();args[slot]=value;r=subprocess.run([str(binary),*map(str,args),str(expected),str(expected)],capture_output=True,timeout=2)
        assert r.returncode==2 and error.encode() in r.stderr
        controls.append({'kind':kind,'args':args,'code':r.returncode,'error':r.stderr.decode()})
    facts={'rust_frames':len(rows),'rust_allocation_bytes':len(rows)*16384,'rust_native_bytes':sum(r['native_bytes'] for r in rows),'rust_negative_controls':len(controls),'rust_core_tests':5,'scope':'Dependency-free Rust frame receipt/allocation and transactional ownership policy; no WASM execution, source compilation, native Canvas sequencing or platform acceptance'}
    atomic(out/'result.json',{'observations':facts,'rows':rows,'controls':controls,'rust_identity':identity,'binary_sha256':digest(binary),'source_sha256':{p.name:digest(p) for p in source.glob('*.rs')}})
    return facts
