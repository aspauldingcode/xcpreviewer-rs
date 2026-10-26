from pathlib import Path
import subprocess,os,plistlib,json
w=Path(__file__).parent
env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')}
(w/'native.bplist').unlink(missing_ok=True)
for name,args,t in [('bridge-build',['xcrun','clang','-arch','arm64','-c',str(w/'bridge.s'),'-o',str(w/'bridge.o')],30),('identity-build',['xcrun','clang','-arch','arm64','-c',str(w/'identity.c'),'-o',str(w/'identity.o')],30),('native-build',['xcrun','swiftc','-module-cache-path',str(w/'module-cache'),'-import-objc-header',str(w/'bridge.h'),str(w/'native.swift'),str(w/'bridge.o'),str(w/'identity.o'),'-Xlinker','-rpath','-Xlinker','/Applications/Xcode.app/Contents','-o',str(w/'native')],30),('native',[str(w/'native'),str(w/'input.bplist'),str(w/'native.bplist')],8)]:
 try:p=subprocess.run(args,capture_output=True,timeout=t,env=env)
 except subprocess.TimeoutExpired as error:
  (w/(name+'.stdout')).write_bytes(error.stdout or b'');(w/(name+'.stderr')).write_bytes((error.stderr or b'')+b'\nOwned subprocess deadline exceeded\n');raise
 (w/(name+'.stdout')).write_bytes(p.stdout);(w/(name+'.stderr')).write_bytes(p.stderr);print(name,p.returncode,(p.stdout+p.stderr).decode()[:1800]);p.check_returncode()
print(plistlib.loads((w/'native.bplist').read_bytes())['destroyedShells'])
