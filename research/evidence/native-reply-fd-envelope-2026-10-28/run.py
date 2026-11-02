from pathlib import Path
import subprocess,os,signal,plistlib,json,sys
w=Path(__file__).parent;env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')}
def run(n,args,t):
 p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,start_new_session=True)
 try:a,b=p.communicate(timeout=t)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGKILL);a,b=p.communicate();(w/(n+'.stdout')).write_bytes(a);(w/(n+'.stderr')).write_bytes(b);raise
 (w/(n+'.stdout')).write_bytes(a);(w/(n+'.stderr')).write_bytes(b);(w/(n+'.status.json')).write_text(json.dumps({'returncode':p.returncode})+'\n');assert p.returncode==0,b.decode()
if '--no-build' not in sys.argv:
 for n,ext in [('bridge','.s'),('identity','.c'),('peer','.m')]:run(n+'-build',['xcrun','clang','-arch','arm64','-fobjc-arc','-fblocks','-c',str(w/(n+ext)),'-o',str(w/(n+'.o'))],30)
 run('native-build',['xcrun','swiftc','-module-cache-path',str(w/'module-cache'),'-import-objc-header',str(w/'bridge.h'),str(w/'native.swift'),str(w/'bridge.o'),str(w/'identity.o'),str(w/'peer.o'),'-Xlinker','-rpath','-Xlinker','/Applications/Xcode.app/Contents','-o',str(w/'native')],30)
for case in ['extra-fd','fd-as-data']:
 mode='reply-first'
 env.pop('OWNED_FD_AS_DATA',None)
 if case=='fd-as-data':env['OWNED_FD_AS_DATA']='1'
 out=w/(case+'.bplist');out.unlink(missing_ok=True);run(case,[str(w/'native'),mode,str(out)],8)
 r=plistlib.loads(out.read_bytes());print(json.dumps({k:r[k] for k in ['mode','callbackCount','captureAliveWhilePending','captureAliveAtReplyWait','captureReleasedAfterCleanup','captureAliveAfterCleanup','captureEvents','nativeKind','originalReferenceDroppedBeforeTrigger']}),flush=True)
