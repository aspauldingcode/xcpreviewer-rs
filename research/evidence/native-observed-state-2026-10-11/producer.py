import pathlib,sys,json,subprocess,hashlib
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
with Controller().lock():
 e=r/'research/evidence/native-observed-state-2026-10-11';binary=r/'research/build/observed-state-reference';compiler='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc'
 x=subprocess.run([compiler,'-sdk','/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk','-module-cache-path',str(r/'research/build/observed-state-module-cache'),'-parse-as-library',str(e/'ObservedStateReference.swift'),'-o',str(binary)],capture_output=True,timeout=60);(e/'compile.json').write_text(json.dumps({'code':x.returncode,'timeout':False,'stdout':x.stdout.decode(),'stderr':x.stderr.decode()},indent=2));x.check_returncode()
 (e/'environment.json').write_text(json.dumps({'compiler':compiler,'compiler_sha256':hashlib.sha256(pathlib.Path(compiler).read_bytes()).hexdigest(),'helper':str(binary),'helper_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'platform':subprocess.check_output(['sw_vers']).decode()},indent=2))
 for i in range(2):
  root=e/f'run-{i}';root.mkdir();x=subprocess.run([str(binary),str(root)],capture_output=True,timeout=15);(root/'wait.json').write_text(json.dumps({'code':x.returncode,'timeout':False,'stdout':x.stdout.decode(),'stderr':x.stderr.decode()},indent=2));print(i,x.returncode,flush=True)
  if x.returncode==0:
   result=json.loads((root/'result.json').read_text());print([(row['phase'],(root/(row['phase']+'.raw')).read_bytes()[:4].hex()) for row in result['rows']],flush=True)
