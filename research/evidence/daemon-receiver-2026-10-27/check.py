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
run('source',['python3',str(w/'source-verify.py')]);run('uv-source',['python3',str(r/'research/evidence/service-xpc-roundtrip-2026-10-24/source-verify.py')]);run('native-check',['python3',str(w/'run-native.py')],60)
x=plistlib.loads((w/'native.bplist').read_bytes());inputs=plistlib.loads((w/'input.bplist').read_bytes());source=json.loads((w/'source-findings.json').read_text())
assert x['relayCalls']==x['lazyCopiesDestroyed']==12 and x['encodedCallbackCalls']==4 and x['replyCopiesDestroyed']==8 and x['parseErrorsReleased']==9
assert (x['lazySize'],x['lazyStride'],x['receiverSize'],x['receiverStride'])==(17,24,16,16)
for n,pin in source['source_images'].items():assert [u for p,u in x['runtimeImages'].items() if p.endswith('/'+n)]==[pin['uuid']]
assert [u for p,u in x['runtimeImages'].items() if p.endswith('/PreviewsServices')]==['fffb683f59433c2591b272d6e5174fa3']
for data,row,receipt in zip(inputs,x['rows'],x['carrierReceipts']):
 assert data['case']==row['case'] and data['data']==row['serializedBytes'] and row['replyPresent']==(data['mode']!='oneway')
 assert row['parseAccepted']==data['case'].endswith('/dictionary')
 if row['parseAccepted']:assert row['canonical']==plistlib.loads(data['data'])
 assert all(receipt[k] for k in ['accepted','uvInitialized','replyBytesAvailable','replyBytesEqual','peerSameProcess']) and receipt['requests']==receipt['callbacks']==1 and not receipt['timedOut'] and receipt['errorsBeforeCleanup']==0
 replies=row['encodedReplies'];assert len(replies)==(1 if data['mode']=='send' else 0)
 if replies:assert replies[0]['payloadPresent'] and not replies[0]['errorPresent'] and replies[0]['summary']['dictionary']=={} and plistlib.loads(replies[0]['summary']['data'])=={}
assert not re.search(r'unknown context at|\$[0-9a-fA-F]{6,}|0x[0-9a-fA-F]{10,}',json.dumps(x['rows'],default=str))
base=['--offline','--locked','--manifest-path',str(r/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(w/'target')]
run('tests',[str(b/'cargo'),'test',*base,*(['--test','daemon_receiver'] if '--replay' in sys.argv else [])],60)
run('example-build',[str(b/'cargo'),'build',*base,'--example','daemon_receiver'],60);run('wasm-build',[str(b/'cargo'),'build',*base,'--target','wasm32-wasip1','--example','daemon_receiver'],60)
out=run('example',[str(w/'target/debug/examples/daemon_receiver')],5);wasm=w/'target/wasm32-wasip1/debug/examples/daemon_receiver.wasm';assert out==run('wasi',['node',str(w/'run-wasi.cjs'),str(wasm)],10)
result={'actual_native_receiver_protocol_calls':12,'native_relay_calls':12,'native_sdk_uv_exchanges':12,'lazy_byte_sequences_compared_in_full':12,'native_lazy_parse_successes':3,'native_lazy_parse_failures':9,'native_reply_copies_destroyed':8,'explicit_unit_reply_callbacks':4,'drop_controls_without_observed_callback':4,'source_bytes_verified':source['source_bytes_verified'],'host_wasi_stdout_equal':True,'rust_tests':sum(map(int,re.findall(r'test result: ok\. (\d+) passed',(w/'tests.stdout').read_text()))),'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest()};(w/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
