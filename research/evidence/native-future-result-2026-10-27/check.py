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
run('snapshot-source',['python3',str(w/'snapshot-source.py')])
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
assert record['stateSize']==58 and record['stateStride']==64 and record['snapshotDispatchOffsets']==[0x115868]
for row,state in zip(inputs,record['states']):
 assert state['beforeSnapshot']=={'state':'running'}
 after=state['afterSnapshot'];assert after['state']=='finished'
 if row['expectedSuccess']:
  assert after['termination']=='succeeded' and after['value']==plistlib.loads(row['responseData'])
 else:
  assert after['termination']=='failed'
  if row['case'] in ['malformed','empty']:assert (after['domain'],after['code'])==('NSCocoaErrorDomain',3840)
  elif row['case']=='absent-with-error':assert after['errorType'].endswith('.HumanReadableNSError') and after['wrappedError']=={'domain':'owned.encoded.reply','code':17,'description':'owned reply failure'}
  else:assert after['errorType'].endswith('.EmptyReply')
 assert not re.search(r'unknown context at|\$[0-9a-fA-F]{6,}|0x[0-9a-fA-F]{10,}',json.dumps(after))
base=['--offline','--locked','--manifest-path',str(r/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(w/'target')]
run('tests',[str(b/'cargo'),'test',*base,*(['--test','native_future_result'] if '--replay' in sys.argv else [])],60)
run('example-build',[str(b/'cargo'),'build',*base,'--example','future_result'],60)
run('wasm-build',[str(b/'cargo'),'build',*base,'--target','wasm32-wasip1','--example','future_result'],60)
output=run('example',[str(w/'target/debug/examples/future_result')],5)
wasm=w/'target/wasm32-wasip1/debug/examples/future_result.wasm';out=run('wasi',['node',str(w/'run-wasi.cjs'),str(wasm)],10);assert output==out
result={'native_sdk_encoded_callbacks':6,'native_snapshot_getter_calls':12,'native_snapshot_original_values_destroyed':12,'running_before':6,'finished_after':6,'succeeded_values_compared_in_full':2,'failed_values_captured':4,'parse_failures':2,'wrapped_remote_failure':1,'empty_reply_failure':1,'mutable_lock_storage_reflected_in_qualified_helper':False,'state_size':58,'state_stride':64,'host_wasi_stdout_equal':True,'rust_tests':sum(map(int,re.findall(r'test result: ok\. (\d+) passed',(w/'tests.stdout').read_text()))),'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest(),'source_bytes_verified':5704}
(w/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
