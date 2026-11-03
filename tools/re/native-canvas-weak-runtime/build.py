"""Build owned weak/FD controls; native execution holds the shared controller lock."""
from pathlib import Path
import argparse,subprocess,hashlib,json,fcntl,shutil
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=a.output.resolve();r.mkdir(exist_ok=False,parents=True);src=Path(__file__).resolve().parent;root=src.parents[2]
for n in ['weak.swift','control.c']:shutil.copy2(src/n,r/n)
key=hashlib.sha256((src/'weak.swift').read_bytes()).hexdigest()[:12];lib=r/('libCanvasWeakProbe_'+key+'.dylib')
def run(label,args,timeout):
 v=subprocess.run(args,capture_output=True,text=True,timeout=timeout);(r/(label+'.stdout')).write_text(v.stdout);(r/(label+'.stderr')).write_text(v.stderr);assert v.returncode==0,(label,v.stderr)
run('swift-build',['xcrun','swiftc','-emit-library','-module-name','CanvasWeakProbe_'+key,str(src/'weak.swift'),'-o',str(lib)],30)
run('control-build',['xcrun','clang',str(src/'control.c'),str(lib),'-lobjc','-o',str(r/'control')],30)
with open(root/'research/state/controller.lock','a+') as f:
 fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);run('controls',[str(r/'control')],5)
receipt={'library':str(lib),'library_sha256':hashlib.sha256(lib.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((src/'weak.swift').read_bytes()).hexdigest(),'controls':3}
(r/'build.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
