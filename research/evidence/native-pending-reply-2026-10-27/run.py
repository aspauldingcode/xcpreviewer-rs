from pathlib import Path
import subprocess,os,plistlib,json
w=Path(__file__).parent;env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')}
def run(n,a,t):
 try:p=subprocess.run(a,capture_output=True,env=env,timeout=t)
 except subprocess.TimeoutExpired as e:
  (w/(n+'.stdout')).write_bytes(e.stdout or b'');(w/(n+'.stderr')).write_bytes(e.stderr or b'');raise
 (w/(n+'.stdout')).write_bytes(p.stdout);(w/(n+'.stderr')).write_bytes(p.stderr);p.check_returncode()

for n,ext in [('bridge','.s'),('identity','.c'),('peer','.m')]:run(n+'-build',['xcrun','clang','-arch','arm64','-fobjc-arc','-fblocks','-c',str(w/(n+ext)),'-o',str(w/(n+'.o'))],30)
run('native-build',['xcrun','swiftc','-module-cache-path',str(w/'module-cache'),'-import-objc-header',str(w/'bridge.h'),str(w/'native.swift'),str(w/'bridge.o'),str(w/'identity.o'),str(w/'peer.o'),'-Xlinker','-rpath','-Xlinker','/Applications/Xcode.app/Contents','-o',str(w/'native')],30)
for mode in ['local-invalidate','remote-close','reply-first']:
 out=w/(mode+'.bplist');out.unlink(missing_ok=True);run(mode,[str(w/'native'),mode,str(out)],8);print(mode,plistlib.loads(out.read_bytes()),flush=True)
