from pathlib import Path
import subprocess,os,signal,re,json,shutil,hashlib
w=Path(__file__).parent;here=Path('/Users/8amps/xcpreviewer-rs/tools/re/swiftui-preview');guard=w/'guard';guard.mkdir(exist_ok=True)
env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')}
def run(args,t,label):
 p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,start_new_session=True)
 try:a,b=p.communicate(timeout=t)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGKILL);a,b=p.communicate();(guard/(label+'.stdout')).write_bytes(a);(guard/(label+'.stderr')).write_bytes(b);raise
 (guard/(label+'.stdout')).write_bytes(a);(guard/(label+'.stderr')).write_bytes(b);assert p.returncode==0,b.decode();return a,b
shutil.copyfile(w/'Source.swift',guard/'Source.swift')
for name in ['Registry.swift','RegistryBridge.s','RegistryBridge.h','RegistryIdentity.c']:shutil.copyfile(here/name,guard/name)
p=guard/'Registry.swift';p.write_text(p.read_text().replace('90f7fa24a2803e8aa62d148b11bfc28d','00000000000000000000000000000000'))
common=['xcrun','swiftc','-parse-as-library','-module-name','Source','-target','arm64-apple-macos14.0','-module-cache-path',str(guard/'module-cache')]
a,b=run(common+['-typecheck','-Xfrontend','-dump-macro-expansions',str(guard/'Source.swift')],30,'expand')
name=re.search(rb'^struct (\$s\S+): DeveloperToolsSupport.PreviewRegistry',b,re.M)[1].decode()
(guard/'Guard.swift').write_text('''import SwiftUI
import DeveloperToolsSupport
@main struct Guard {
 @MainActor static func main() {
  do { _ = try RegistryBridge.content(`__NAME__`.self);fatalError("Unexpected guard success") }
  catch RegistryBridge.Failure.unsupportedRuntime { print("unsupportedRuntime") }
  catch {fatalError("Unexpected guard error: \\(error)")}
 }
}
'''.replace('__NAME__',name))
for name in ['RegistryBridge.s','RegistryIdentity.c']:run(['xcrun','clang','-arch','arm64','-c',str(guard/name),'-o',str(guard/(name+'.o'))],30,name)
run(common+['-import-objc-header',str(guard/'RegistryBridge.h'),str(guard/'Source.swift'),str(guard/'Guard.swift'),str(guard/'Registry.swift'),str(guard/'RegistryBridge.s.o'),str(guard/'RegistryIdentity.c.o'),'-o',str(guard/'guard')],30,'build')
a,b=run([str(guard/'guard')],8,'guard');assert a==b'unsupportedRuntime\n' and b'Registry capture: invoke' not in b
(w/'guard-results.json').write_text(json.dumps({'passed':True,'expected_error':'unsupportedRuntime','production_adapter_copy':True,'only_expected_uuid_changed':True,'framework_unchanged':True,'body_invocation_trace_absent':True,'scope':'Copied production adapter native guard; not the full producer CLI. The earlier full-CLI wrong-profile attempt ended at a compile deadline, not this guard.'},indent=2)+'\n');print('Wrong-runtime adapter guard rejected before body invocation')
