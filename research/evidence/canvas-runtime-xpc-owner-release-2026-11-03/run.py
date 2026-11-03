"""Bounded native public-XPC component execution in owned processes only."""
from pathlib import Path
import argparse,subprocess,os,signal,json,hashlib,fcntl,shutil,sys
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=a.output.resolve();r.mkdir(exist_ok=False,parents=True);src=Path(__file__).resolve().parent;root=src.parents[2]
for n in ['probe.m','run.py','verify.py']:shutil.copy2(src/n,r/n)
def run(name,args,seconds):
 q=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 try:out,err=q.communicate(timeout=seconds);timeout=False
 except subprocess.TimeoutExpired:os.killpg(q.pid,signal.SIGKILL);out,err=q.communicate();timeout=True
 (r/(name+'.stdout')).write_bytes(out);(r/(name+'.stderr')).write_bytes(err);v={'pid':q.pid,'code':q.returncode,'timeout':timeout};(r/(name+'.result.json')).write_text(json.dumps(v,indent=2)+'\n');assert q.returncode==0 and not timeout,(name,v)
run('compile',['xcrun','clang','-fblocks','-fno-objc-arc','-framework','Foundation',str(r/'probe.m'),'-o',str(r/'probe')],30)
with open(root/'research/state/controller.lock','a+') as f:
 fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for mode in ['normal','cancel-inflight','cancel-pending','release-inflight','release-pending']:run(mode,[str(r/'probe'),mode],8)
checked=subprocess.run([sys.executable,str(r/'verify.py'),str(r),'--owner-release'],capture_output=True,text=True,timeout=8,check=True);verified=json.loads(checked.stdout);assert len(verified)==5;(r/'verification.json').write_text(checked.stdout)
(r/'receipt.json').write_text(json.dumps({'classification':'native_public_sdk_component_execution','source_sha256':hashlib.sha256((r/'probe.m').read_bytes()).hexdigest(),'private_canvas_invoked':False},indent=2)+'\n')
print('Five owned native XPC controls returned zero; full five-mode recorded assertions passed.')
