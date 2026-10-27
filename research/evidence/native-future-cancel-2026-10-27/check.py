from pathlib import Path
import subprocess,os,json,plistlib,hashlib,re,sys
w=Path(__file__).parent;r=Path('/Users/8amps/xcpreviewer-rs');b=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin');env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')};env.update(RUSTC=str(b/'rustc'),RUSTDOC=str(b/'rustdoc'))
def run(n,args,t=30):
 try:p=subprocess.run(args,cwd=r,env=env,capture_output=True,timeout=t)
 except subprocess.TimeoutExpired as e:
  (w/(n+'.stdout')).write_bytes(e.stdout or b'');(w/(n+'.stderr')).write_bytes(e.stderr or b'');raise
 (w/(n+'.stdout')).write_bytes(p.stdout);(w/(n+'.stderr')).write_bytes(p.stderr)
 if p.returncode:print(n,(p.stdout+p.stderr).decode(errors='replace')[-2000:])
 p.check_returncode();return p.stdout
for name in ['source-verify','extra-source','snapshot-source','transition-source','cancel-source']:run(name,['python3',str(w/(name+'.py'))])
run('reply-source',['python3',str(r/'research/evidence/transport-reply-2026-10-24/verify.py')]);run('uv-source',['python3',str(r/'research/evidence/service-xpc-roundtrip-2026-10-24/source-verify.py')])
run('native-check',['python3',str(w/'run-native.py')],60)
x=plistlib.loads((w/'native.bplist').read_bytes());source=json.loads((w/'source-findings.json').read_text())
assert x['calls']==x['futureReferencesReleased']==x['delayedReplyCopiesDestroyed']==12
assert x['snapshotCalls']==84 and x['encodedCallbackCalls']==36
assert x['cancelCalls']==24 and x['cancelDispatchOffsets']==[0x34178]
assert len(x['repeatedStates'])==12 and len(x['carrierReceipts'])==24
for n,pin in source['source_images'].items():assert [u for p,u in x['runtimeImages'].items() if p.endswith('/'+n)]==[pin['uuid']]
assert [u for p,u in x['runtimeImages'].items() if p.endswith('/PreviewsServices')]==['fffb683f59433c2591b272d6e5174fa3']
for cancellation,row in zip(x['cancellationStates'],x['repeatedStates']):
 assert cancellation['case']==row['case']
 assert len(cancellation['steps'])==2 and cancellation['steps'][0]==cancellation['steps'][1]
 if cancellation['order']=='before':
  expected={'state':'finished','termination':'canceled','callsite':{'file':'owned','function':'owned','line':1,'column':1}}
  assert row['first']==expected and all(step==expected for step in cancellation['steps'])
 else:assert all(step==row['first'] for step in cancellation['steps'])
 assert row['first']==row['afterLaterDictionary']==row['afterEmptyReply']
 assert row['first']['state']=='finished'
 assert not re.search(r'unknown context at|\$[0-9a-fA-F]{6,}|0x[0-9a-fA-F]{10,}',json.dumps(row))
assert sum(s['first']['termination']=='succeeded' for s in x['repeatedStates'])==2
for receipt in x['carrierReceipts']:
 assert all(receipt[k] for k in ['accepted','uvInitialized','replyBytesAvailable','replyBytesEqual','peerSameProcess'])
 assert receipt['requests']==receipt['callbacks']==1 and receipt['errorsBeforeCleanup']==0 and not receipt['timedOut']
if '--record-fixture' in sys.argv:(r/'tools/re/rust/canvas-core/tests/fixtures/native_future_cancel/native.bplist').write_bytes((w/'native.bplist').read_bytes())
base=['--offline','--locked','--manifest-path',str(r/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(w/'target')]
run('tests',[str(b/'cargo'),'test',*base,*(['--test','native_future_cancel'] if '--replay' in sys.argv else [])],60)
run('example-build',[str(b/'cargo'),'build',*base,'--example','native_future_cancel'],60);run('wasm-build',[str(b/'cargo'),'build',*base,'--target','wasm32-wasip1','--example','native_future_cancel'],60)
out=run('example',[str(w/'target/debug/examples/native_future_cancel')],5);wasm=w/'target/wasm32-wasip1/debug/examples/native_future_cancel.wasm';assert out==run('wasi',['node',str(w/'run-wasi.cjs'),str(wasm)],10)
result={'native_cancellation_calls':24,'native_encoded_callback_invocations':36,'native_sdk_uv_exchanges':24,'native_snapshot_getter_calls':84,'cancel_before_first_reply_retained':6,'cancel_after_completion_result_retained':6,'second_cancel_callsite_did_not_replace_first':6,'source_bytes_verified':7580+284,'new_cancel_source_bytes':284,'host_wasi_stdout_equal':True,'rust_tests':sum(map(int,re.findall(r'test result: ok\. (\d+) passed',(w/'tests.stdout').read_text()))),'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest()};(w/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
