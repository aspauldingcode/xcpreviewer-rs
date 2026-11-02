from pathlib import Path
import os,subprocess,json,fcntl,hashlib,sys,time,signal
r=Path(__file__).parent;env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')}
p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');assert hashlib.sha256(p.read_bytes()).hexdigest()=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
def run(label,args,deadline):
 start=time.monotonic()
 q=subprocess.Popen(args,cwd=r,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 try:out,err=q.communicate(timeout=deadline);code=q.returncode;timeout=False
 except subprocess.TimeoutExpired:
  os.killpg(q.pid,signal.SIGKILL);out,err=q.communicate();code=q.returncode;timeout=True
 (r/(label+'.stdout')).write_bytes(out);(r/(label+'.stderr')).write_bytes(err);rec={'code':code,'timeout':timeout,'elapsed_seconds':time.monotonic()-start,'pid':q.pid};(r/(label+'.result.json')).write_text(json.dumps(rec,indent=2)+'\n');print(label,json.dumps(rec),flush=True);return rec
if '--no-build' not in sys.argv:
 for label,args in [('bridge-build',['xcrun','clang','-arch','arm64','-c','bridge.s','-o','bridge.o']),('identity-build',['xcrun','clang','-arch','arm64','-c','identity.c','-o','identity.o']),('native-build',['xcrun','swiftc','-module-cache-path',str(r/'module-cache'),'-import-objc-header','bridge.h','native.swift','bridge.o','identity.o','-Xlinker','-rpath','-Xlinker','/Applications/Xcode.app/Contents','-o','native'])]:
  if run(label,args,30)['code']!=0:sys.exit(1)
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for mode in ([a for a in sys.argv[1:] if a!='--no-build'] or ['invalidate','cancel','owner-loss','drop-waiting-token','ordering','reentrant','inflight','race','cancel-reentry']):
  if mode=='--no-build':continue
  rec=run('native-'+mode,[str(r/'native'),mode],8)
  rows=[json.loads(x) for x in (r/('native-'+mode+'.stdout')).read_text().splitlines()]
  if mode.startswith('policy-'):
   assert not rec['timeout'] and any(x['event']=='policy-release-begin' for x in rows)
  elif mode=='cancel-reentry':
   assert rec['code']!=0 and not rec['timeout'] and any(x['event']=='destructor-reentry-begin' for x in rows) and not any(x['event']=='pass' for x in rows)
  else:
   assert rec['code']==0 and not rec['timeout'] and rows[-1]['event']=='pass' and rows[-1]['mode']==mode
print('Requested native controls completed; inspect individual outcomes and verify.py assertions.')
