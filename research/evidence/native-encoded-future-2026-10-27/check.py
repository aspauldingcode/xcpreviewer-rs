from pathlib import Path
import subprocess,os,json,plistlib,hashlib,re,sys
w=Path(__file__).parent;r=Path('/Users/8amps/xcpreviewer-rs');b=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin');env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')};env.update(RUSTC=str(b/'rustc'),RUSTDOC=str(b/'rustdoc'))
def run(n,args,t=30):
 try:p=subprocess.run(args,cwd=r,env=env,capture_output=True,timeout=t)
 except subprocess.TimeoutExpired as e:
  (w/(n+'.stdout')).write_bytes(e.stdout or b'');(w/(n+'.stderr')).write_bytes(e.stderr or b'');raise
 (w/(n+'.stdout')).write_bytes(p.stdout);(w/(n+'.stderr')).write_bytes(p.stderr)
 if p.returncode:print(n,(p.stdout+p.stderr).decode(errors='replace')[-1600:])
 p.check_returncode();return p.stdout
run('source',['python3',str(w/'source-verify.py')])
run('reply-source',['python3',str(r/'research/evidence/transport-reply-2026-10-24/verify.py')])
run('uv-source',['python3',str(r/'research/evidence/service-xpc-roundtrip-2026-10-24/source-verify.py')])
run('extra-source',['python3',str(w/'extra-source.py')])
run('native-check',['python3',str(w/'run-native.py')],60)
record=plistlib.loads((w/'native.bplist').read_bytes());inputs=plistlib.loads((w/'input.bplist').read_bytes());source=json.loads((w/'source-findings.json').read_text())
assert record['calls']==record['futureReferencesReleased']==record['delayedReplyCopiesDestroyed']==6
for name,pin in source['source_images'].items():assert [u for p,u in record['runtimeImages'].items() if p.endswith('/'+name)]==[pin['uuid']]
assert [u for p,u in record['runtimeImages'].items() if p.endswith('/PreviewsServices')]==['fffb683f59433c2591b272d6e5174fa3']
assert [s['successfulAfterEncodedCallback'] for s in record['states']]==[True,True,False,False,False,False]
for row,state,receipt in zip(inputs,record['states'],record['carrierReceipts']):
 assert state['case']==row['case'] and not state['successfulBeforeEncodedCallback']
 assert all(receipt[k] for k in ['accepted','uvInitialized','replyBytesAvailable','replyBytesEqual','peerSameProcess'])
 assert receipt['requests']==receipt['callbacks']==1 and receipt['errorsBeforeCleanup']==0 and not receipt['timedOut']
base=['--offline','--locked','--manifest-path',str(r/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(w/'target')]
run('tests',[str(b/'cargo'),'test',*base,*(['--test','native_encoded_future'] if '--replay' in sys.argv else [])],60)
run('example-build',[str(b/'cargo'),'build',*base,'--example','encoded_reply'],60)
run('wasm-build',[str(b/'cargo'),'build',*base,'--target','wasm32-wasip1','--example','encoded_reply'],60)
output=run('example',[str(w/'target/debug/examples/encoded_reply')],5)
wasm=w/'target/wasm32-wasip1/debug/examples/encoded_reply.wasm';out=run('wasi',['node',str(w/'run-wasi.cjs'),str(wasm)],10);assert output==out
result={'native_sdk_encoded_callbacks':6,'native_success_predicate_true':2,'native_success_predicate_false_not_terminal_proof':4,'original_reply_and_callsite_destroyed_before_sdk_and_callback':6,'closure_context_references_released':6,'uv_objects_retained_across_sdk_cleanup':6,'empty_received_uv_initialized':True,'portable_ack_success':4,'portable_typed_success':2,'portable_typed_errors':4,'host_wasi_stdout_equal':True,'rust_tests':sum(map(int,re.findall(r'test result: ok\. (\d+) passed',(w/'tests.stdout').read_text()))),'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest(),'source_bytes_verified':3060+1716+160+504}
(w/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
