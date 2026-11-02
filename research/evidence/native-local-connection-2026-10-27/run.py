from pathlib import Path
import subprocess,os,plistlib,json
w=Path(__file__).parent;env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')}
def run(n,a,t):
 try:p=subprocess.run(a,capture_output=True,env=env,timeout=t)
 except subprocess.TimeoutExpired as e:
  (w/(n+'.stdout')).write_bytes(e.stdout or b'');(w/(n+'.stderr')).write_bytes(e.stderr or b'');raise
 (w/(n+'.stdout')).write_bytes(p.stdout);(w/(n+'.stderr')).write_bytes(p.stderr);p.check_returncode()
for n,ext in [('bridge','.s'),('identity','.c')]:run(n+'-build',['xcrun','clang','-arch','arm64','-c',str(w/(n+ext)),'-o',str(w/(n+'.o'))],30)
results={}
for direction in ['outgoing','incoming']:
 run('peer-'+direction+'-build',['xcrun','clang','-arch','arm64','-fobjc-arc','-fblocks','-c',str(w/('peer-'+direction+'.m')),'-o',str(w/'peer.o')],30)
 run('native-'+direction+'-build',['xcrun','swiftc','-module-cache-path',str(w/'module-cache'),'-import-objc-header',str(w/'bridge.h'),str(w/'native.swift'),str(w/'bridge.o'),str(w/'identity.o'),str(w/'peer.o'),'-Xlinker','-rpath','-Xlinker','/Applications/Xcode.app/Contents','-o',str(w/'native')],30)
 for profile in ['valid','malformed','empty','missing']:
  env['OWNED_REPLY_PROFILE']=profile;label=direction+'-'+profile
  out=w/(label+'.bplist');out.unlink(missing_ok=True)
  run(label,[str(w/'native'),'-',str(out)],8)
  d=plistlib.loads(out.read_bytes());print(label,d,flush=True);results[label]=d
(w/'results.raw.json').write_text(json.dumps(results,default=lambda d:d.hex(),indent=2)+'\n')
