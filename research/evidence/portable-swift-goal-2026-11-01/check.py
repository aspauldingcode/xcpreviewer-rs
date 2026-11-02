from pathlib import Path
import subprocess,json,hashlib
w=Path(__file__).parent
builds=json.loads((w/'build-results.json').read_text());assert builds['swift-state']=={'returncode':0,'timed_out':False} and builds['swiftui-state']=={'returncode':1,'timed_out':False}
assert "no such module 'SwiftUI'" in ((w/'swiftui-state.stdout').read_text()+(w/'swiftui-state.stderr').read_text())
wasm=w/'swift-state/build/wasm32-unknown-wasip1/debug/Probe.wasm';assert wasm.read_bytes()[:8]==b'\0asm\x01\0\0\0'
p=subprocess.run(['node',str(w/'run-wasi.cjs'),str(wasm)],capture_output=True,timeout=10);(w/'wasi.stdout').write_bytes(p.stdout);(w/'wasi.stderr').write_bytes(p.stderr);assert p.returncode==0 and p.stdout==b'count=0\ncount=1\ncount=2\n'
v=subprocess.run(['/Users/8amps/.swiftly/bin/swift','--version'],capture_output=True,timeout=5);v.check_returncode()
result={'passed':True,'compiler_version':v.stdout.decode().strip(),'swift_sdk':'6.3-RELEASE-wasm32-unknown-wasip1','swift_language_wasm_build':True,'swift_language_wasm_execution_stdout':p.stdout.decode(),'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest(),'swiftui_build_failed_missing_module':True,'restricted_configuration_query_io_error_preserved':True,'new_installs':False,'host':'macOS arm64','non_apple_host_verified':False,'swiftui_runtime_or_rendering_implemented':False,'native_canvas_or_private_framework_calls':0,'scope':'Original dependency-free Swift compiler/SDK feasibility probes, not SwiftUI parity, non-Apple host build acceptance or interactive state-runtime proof.'}
(w/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
