import sys,pathlib,json,subprocess,hashlib
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
with Controller().lock():
 e=r/'research/evidence/surface-full-failure-2026-10-11';binary=r/'research/build/surface-full-failure';compiler='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang'
 args=[compiler,'-isysroot','/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk','-std=c11','-Wall','-Wextra','-framework','CoreFoundation','-framework','IOSurface','-lbsm',str(e/'full_failure_probe.c'),'-o',str(binary)]
 x=subprocess.run(args,capture_output=True,timeout=60);(e/'compile.json').write_text(json.dumps({'argv':args,'code':x.returncode,'timeout':False,'stdout':x.stdout.decode(),'stderr':x.stderr.decode()},indent=2)+'\n');x.check_returncode()
 (e/'environment.json').write_text(json.dumps({'compiler':compiler,'compiler_sha256':hashlib.sha256(pathlib.Path(compiler).read_bytes()).hexdigest(),'helper':str(binary),'helper_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'platform':sys.platform,'scope':'Owned CPU surfaces and audited fork/exec peer only; no Xcode workspace'},indent=2)+'\n')
 x=subprocess.run([str(binary),'17','9','49','batch',str(e)],capture_output=True,timeout=15);(e/'wait.json').write_text(json.dumps({'code':x.returncode,'timeout':False,'stdout':x.stdout.decode(),'stderr':x.stderr.decode()},indent=2)+'\n');print(x.returncode,x.stdout.decode(),x.stderr.decode(),flush=True)
