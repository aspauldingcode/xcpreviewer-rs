from pathlib import Path
import subprocess,json,os,signal,fcntl
w=Path(__file__).parent;r=Path('/Users/8amps/xcpreviewer-rs')
def run(name,args,deadline):
 p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')})
 timed=False
 try:a,b=p.communicate(timeout=deadline)
 except subprocess.TimeoutExpired:
  timed=True
  try:os.killpg(p.pid,signal.SIGKILL)
  except ProcessLookupError:pass
  a,b=p.communicate()
 (w/(name+'.stdout')).write_bytes(a);(w/(name+'.stderr')).write_bytes(b);(w/(name+'.status.json')).write_text(json.dumps({'returncode':p.returncode,'timed_out':timed,'deadline_seconds':deadline})+'\n')
 assert not timed and p.returncode==0,(name,b.decode(errors='replace'))
with (r/'research/state/controller.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if '--skip-source' not in __import__('sys').argv:run('source',['python3',str(r/'research/evidence/uv-property-list-2026-10-24/verify.py')],60)
 run('compile',['xcrun','clang','-fobjc-arc','-fblocks','-framework','Foundation',str(w/'control.m'),'-o',str(w/'control')],30)
 run('native',[str(w/'control'),str(w/'native.bplist')],8)
print('Source and two native controls passed; controller released')
