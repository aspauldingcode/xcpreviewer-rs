import sys,json,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,'tools/re');from reloop.core import Controller,atomic
with Controller().lock():
 e=Path('research/evidence/native-state-scheme-2026-10-14');build=Path('research/build/native-state-scheme-2026-10-14');build.mkdir();binary=build/'state-scheme';p=Path('research/loop/continuous.json')
 compiler=Path('/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc');sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest();assert sha(compiler)=='2ed38571e92c0283091838c1649e27650ad9c99950288e883c7b2dc6c4ce89fb'
 d=json.loads(p.read_text());d['state_scheme_checkpoint']['budget']['compile_used']=1;atomic(p,d)
 args=[str(compiler),'-sdk','/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk','-module-cache-path',str(build/'module-cache'),'-parse-as-library','tools/re/fixtures/StateSchemeReference.swift','-o',str(binary)]
 r=subprocess.run(args,capture_output=True,text=True,timeout=60);atomic(e/'compile.json',{'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'argv':args});print('compile',r.returncode,r.stderr,flush=True);r.check_returncode()
 for i in range(2):
  d=json.loads(p.read_text());d['state_scheme_checkpoint']['budget']['native_used']+=1;atomic(p,d)
  out=e/('run-'+str(i));out.mkdir();r=subprocess.run([str(binary.resolve()),str(out.resolve()),'-ApplePersistenceIgnoreState','YES'],capture_output=True,text=True,timeout=15);atomic(out/'wait.json',{'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});print('native',i,r.returncode,r.stderr,flush=True)
 atomic(e/'environment.json',{'compiler':str(compiler),'compiler_sha256':sha(compiler),'binary':str(binary.resolve()),'binary_sha256':sha(binary),'macos':subprocess.check_output(['sw_vers','-productVersion'],text=True).strip(),'build':subprocess.check_output(['sw_vers','-buildVersion'],text=True).strip()})
