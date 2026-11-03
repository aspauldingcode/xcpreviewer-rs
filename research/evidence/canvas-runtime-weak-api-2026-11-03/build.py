"""Build owned fixture and C weak-runtime ABI controls. No target image injection."""
from pathlib import Path
import argparse, subprocess, hashlib, json, fcntl, shutil
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
r=a.output.resolve();r.mkdir(exist_ok=False,parents=True);src=Path(__file__).resolve().parent;root=src.parents[2]
fixture=src.parent/'native-canvas-weak-runtime/weak.swift'
for s in [fixture,src/'control.c',src/'identity.c']:shutil.copy2(s,r/s.name)
key=hashlib.sha256(fixture.read_bytes()).hexdigest()[:12];lib=r/('libCanvasWeakProbe_'+key+'.dylib')
def run(label,args,seconds):
 v=subprocess.run(args,capture_output=True,text=True,timeout=seconds)
 (r/(label+'.stdout')).write_text(v.stdout);(r/(label+'.stderr')).write_text(v.stderr)
 assert v.returncode==0,(label,v.returncode,v.stderr)
run('swift-build',['xcrun','swiftc','-emit-library','-module-name','CanvasWeakProbe_'+key,str(r/'weak.swift'),'-o',str(lib)],30)
run('control-build',['xcrun','clang',str(r/'control.c'),str(r/'identity.c'),str(lib),'-lobjc','-o',str(r/'control')],30)
with open(root/'research/state/controller.lock','a+') as f:
 fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);run('controls',[str(r/'control')],5)
rows=[json.loads(x) for x in (r/'controls.stdout').read_text().splitlines()]
assert rows[0]['main_queue_export_matches'] is True
assert [x['mode'] for x in rows[1:]]==[0,1,2] and all(x['passed'] for x in rows[1:])
receipt={'library':str(lib),'library_sha256':hashlib.sha256(lib.read_bytes()).hexdigest(),'fixture_source_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'controls':3,'runtime':rows[0]}
(r/'build.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
