import sys,pathlib,json,subprocess,hashlib
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
with Controller().lock():
 e=r/'research/evidence/surface-global-id-2026-10-11';binary=r/'research/build/surface-global-id';compiler='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang'
 args=[compiler,'-isysroot','/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk','-std=c11','-Wall','-Wextra','-framework','CoreFoundation','-framework','IOSurface','-lbsm',str(e/'global_id_probe.c'),'-o',str(binary)]
 x=subprocess.run(args,capture_output=True,timeout=60);(e/'compile.json').write_text(json.dumps({'argv':args,'code':x.returncode,'timeout':False,'stdout':x.stdout.decode(),'stderr':x.stderr.decode()},indent=2)+'\n');x.check_returncode()
 (e/'environment.json').write_text(json.dumps({'compiler':compiler,'compiler_sha256':hashlib.sha256(pathlib.Path(compiler).read_bytes()).hexdigest(),'helper':str(binary),'helper_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'platform':sys.platform,'scope':'Owned CPU global-ID lifetime control, no user processes/workspaces'},indent=2)+'\n')
 for name in ['released-0','held','released-1']:
  root=e/name;mode='held' if name=='held' else 'released';x=subprocess.run([str(binary),mode,str(root)],capture_output=True,timeout=15);(root/'wait.json').write_text(json.dumps({'code':x.returncode,'timeout':False,'stdout':x.stdout.decode(),'stderr':x.stderr.decode()},indent=2)+'\n');print(name,x.returncode,x.stdout.decode()[:700],x.stderr.decode(),flush=True)
