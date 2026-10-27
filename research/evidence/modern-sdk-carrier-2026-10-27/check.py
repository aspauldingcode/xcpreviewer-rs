from pathlib import Path
import subprocess,os,plistlib,json,struct,hashlib
w=Path(__file__).parent;r=Path('/Users/8amps/xcpreviewer-rs');b=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin')
env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')};env.update(RUSTC=str(b/'rustc'),RUSTDOC=str(b/'rustdoc'))
def run(name,args,timeout=30):
 try:p=subprocess.run(args,cwd=r,env=env,capture_output=True,timeout=timeout)
 except subprocess.TimeoutExpired as e:
  (w/(name+'.stdout')).write_bytes(e.stdout or b'');(w/(name+'.stderr')).write_bytes(e.stderr or b'');raise
 (w/(name+'.stdout')).write_bytes(p.stdout);(w/(name+'.stderr')).write_bytes(p.stderr);p.check_returncode();return p.stdout
# Existing independently qualified modern update/Unit/ownership and UV pointer-gate source proofs.
run('source',['python3',str(w/'source-verify.py')])
run('uv-source',['python3',str(r/'research/evidence/service-xpc-roundtrip-2026-10-24/source-verify.py')])
base=['--offline','--locked','--manifest-path',str(r/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(w/'target')]
run('cli-build',[str(b/'cargo'),'build',*base,'--bin','inspect-service-message'],60)
run('wasm-build',[str(b/'cargo'),'build',*base,'--target','wasm32-wasip1','--bin','inspect-service-message'],60)
cli=w/'target/debug/inspect-service-message';wasm=w/'target/wasm32-wasip1/debug/inspect-service-message.wasm'
original=plistlib.loads((w/'input.bplist').read_bytes());assert len(original)==2 and all(x['mode']=='delayed' for x in original)
for row in original:row.pop('carrierWire',None)
def typed(v,key=''):
 if isinstance(v,dict):return ('dict',tuple(sorted((k,typed(x,k)) for k,x in v.items())))
 if isinstance(v,list):
  values=[typed(x) for x in v];return ('array',tuple(sorted(values) if key in ['sourceFilePaths','linkerFlags'] else values))
 if isinstance(v,float):return ('float',struct.pack('>d',v).hex())
 return (type(v).__name__,v)
source=json.loads((w/'source-findings.json').read_text())
def native(label,inputs):
 (w/'input.bplist').write_bytes(plistlib.dumps(inputs,fmt=plistlib.FMT_BINARY))
 run(label,['python3',str(w/'run-native.py')],60)
 result=plistlib.loads((w/'native.bplist').read_bytes());(w/(label+'.bplist')).write_bytes((w/'native.bplist').read_bytes())
 for name,pin in source['source_images'].items():assert [u for p,u in result['runtimeImages'].items() if p.endswith('/'+name)]==[pin['uuid']]
 assert [u for p,u in result['runtimeImages'].items() if p.endswith('/PreviewsServices')]==['fffb683f59433c2591b272d6e5174fa3']
 assert result['calls']==result['futureReferencesReleased']==result['delayedReplyCopiesDestroyed']==2
 assert [v['payload']['__unique_service_message_identifier'] for v in result['received']]==['0','1']
 for request,state,receipt in zip(result['received'],result['states'],result['carrierReceipts']):
  assert not state['successfulBeforeOwnedDelayedReply'] and state['successfulAfterOwnedDelayedReply']
  assert receipt['accepted'] and receipt['requests']==receipt['callbacks']==1 and receipt['errorsBeforeCleanup']==0 and not receipt['timedOut'] and receipt['peerSameProcess']
  assert typed(request)==typed(receipt['request'])
  assert receipt['reply']=={'ownedAcceptedIdentifier':request['payload']['__unique_service_message_identifier']}
 return result
first=native('native-wire',original);prepared=[]
for i,(row,request) in enumerate(zip(original,first['received'])):
 path=w/(str(i)+'.request.bplist');path.write_bytes(plistlib.dumps(request,fmt=plistlib.FMT_BINARY))
 canonical=run('canonical-cli-'+str(i),[str(cli),'--canonical',str(path)],8);assert typed(plistlib.loads(canonical))==typed(request)
 out=w/(str(i)+'.wasi.bplist');run('canonical-wasi-'+str(i),['node',str(w/'run-wasi.cjs'),str(wasm),str(path),str(out),'canonical'],10)
 assert typed(plistlib.loads(out.read_bytes()))==typed(request)
 prepared.append(dict(row,carrierWire=out.read_bytes()))
second=native('wasi-wire',prepared)
# Restore stable replay input rather than persisting generated adapter bytes as input assumptions.
(w/'input.bplist').write_bytes(plistlib.dumps(original,fmt=plistlib.FMT_BINARY))
result={'native_future_sdk_compositions':4,'native_wire_sdk_messages':2,'wasi_wire_sdk_messages':2,'sdk_reply_callbacks':4,'source_shell_destroyed_before_sdk_exchange':4,'successful_after_sdk_ack_before_owned_forward':0,'successful_after_owned_unit_forward':4,'reply_value_copies_destroyed':4,'future_references_released':4,'cli_canonical':2,'wasi_canonical':2,'source_bytes_reverified':source['verified_bytes']+160,'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest(),'full_rust_suite_rerun':False,'scope':'Owned adapter synchronously waits for SDK acknowledgement then invokes native Unit reply. No DaemonConnection, native encoded reply decoder, Apple service acknowledgement, provider application, rights settlement or browser WASM claimed.'}
(w/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
