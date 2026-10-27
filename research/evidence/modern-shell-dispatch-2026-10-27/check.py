from pathlib import Path
import subprocess,os,json,plistlib,re,struct
w=Path(__file__).parent;r=Path('/Users/8amps/xcpreviewer-rs');b=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin');env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')};env.update(RUSTC=str(b/'rustc'),RUSTDOC=str(b/'rustdoc'))
def run(n,a,t=60):
 try:p=subprocess.run(a,cwd=r,env=env,capture_output=True,timeout=t)
 except subprocess.TimeoutExpired as e:
  (w/(n+'.stdout')).write_bytes(e.stdout or b'');(w/(n+'.stderr')).write_bytes(e.stderr or b'');raise
 (w/(n+'.stdout')).write_bytes(p.stdout);(w/(n+'.stderr')).write_bytes(p.stderr)
 if p.returncode:print(n,(p.stdout+p.stderr).decode(errors='replace')[-1500:])
 p.check_returncode();return p
run('source',['python3',str(w/'source-verify.py')],30)
run('native-check',['python3',str(w/'run-native.py')],60)
a=plistlib.loads((w/'native.bplist').read_bytes());source=json.loads((w/'source-findings.json').read_text());
for name,identity in source['source_images'].items():
 matches=[uuid for path,uuid in a['runtimeImages'].items() if path.endswith('/'+name)];assert matches==[identity['uuid']]
inputs=plistlib.loads((w/'input.bplist').read_bytes());assert a['calls']==6 and a['futureReferencesReleased']==6 and a['delayedReplyCopiesDestroyed']==2
assert [x['payload']['__unique_service_message_identifier'] for x in a['received']]==list(map(str,range(6)))
for row,request,state in zip(inputs,a['received'],a['states']):
 assert request['messageType']=='update' and row['mode']==state['mode']
 assert state['successfulBeforeOwnedDelayedReply']==(row['mode']=='immediate')
 assert state['successfulAfterOwnedDelayedReply']==(row['mode']!='none')
base=['--offline','--locked','--manifest-path',str(r/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(w/'target')]
run('tests',[str(b/'cargo'),'test',*base,*(['--test','modern_shell_dispatch'] if '--replay' in __import__('sys').argv else [])])
run('wasm-build',[str(b/'cargo'),'build',*base,'--target','wasm32-wasip1','--bin','inspect-service-message'])
run('cli-build',[str(b/'cargo'),'build',*base,'--bin','inspect-service-message'])
cli=w/'target/debug/inspect-service-message';wasm=w/'target/wasm32-wasip1/debug/inspect-service-message.wasm'
def typed(v,key=""):
 if isinstance(v,dict):return ('dict',tuple(sorted((k,typed(x,k)) for k,x in v.items())))
 if isinstance(v,list):
  a=list(map(typed,v));return ('array',tuple(sorted(a) if key in ['sourceFilePaths','linkerFlags'] else a))
 if isinstance(v,float):return ('float',struct.pack('>d',v).hex())
 return (type(v).__name__,v)
prepared=[]
for i,(request,row) in enumerate(zip(a['received'],inputs)):
 p=w/(str(i)+'.received.bplist');p.write_bytes(plistlib.dumps(request,fmt=plistlib.FMT_BINARY));canonical=run('cli-'+str(i),[str(cli),'--canonical',str(p)],8).stdout;assert typed(plistlib.loads(canonical))==typed(request)
 out=w/(str(i)+'.wasi.bplist');run('wasi-'+str(i),['node',str(w/'run-wasi.cjs'),str(wasm),str(p),str(out),'canonical'],10);assert typed(plistlib.loads(out.read_bytes()))==typed(request)
 expected=dict(row['input']);actual=dict(request['payload']);del actual['__unique_service_message_identifier'];assert typed(actual)==typed(expected)
 shell=w/(str(i)+'.shell.bplist');shell.write_bytes(plistlib.dumps(row['input'],fmt=plistlib.FMT_BINARY))
 p2=run('prepare-cli-'+str(i),[str(cli),'--prepare-update',str(shell)],8).stdout
 desired=dict(request);desired['payload']=dict(request['payload']);desired['payload']['__unique_service_message_identifier']='0'
 assert typed(plistlib.loads(p2))==typed(desired)
 out2=w/(str(i)+'.prepared-wasi.bplist');run('prepare-wasi-'+str(i),['node',str(w/'run-wasi.cjs'),str(wasm),str(shell),str(out2),'prepare'],10);assert typed(plistlib.loads(out2.read_bytes()))==typed(desired)
 prepared.append({'kind':'service-shell','input':plistlib.loads(out2.read_bytes())})
d=w/'envelope';d.mkdir(exist_ok=True)
import shutil
for name in ['bridge.s','bridge.h','identity.c','native.swift','run-native.py']:
 shutil.copy2(r/'research/evidence/native-shell-service-2026-10-26'/name,d/name)
(d/'input.bplist').write_bytes(plistlib.dumps(prepared,fmt=plistlib.FMT_BINARY))
run('prepared-native-check',['python3',str(d/'run-native.py')],60)
roundtrip=plistlib.loads((d/'native.bplist').read_bytes())['rows'];assert len(roundtrip)==6
for original,row in zip(prepared,roundtrip):assert row['accepted'] and typed(original['input'])==typed(row['canonical'])
results={'prepared_native_roundtrips':6,'prepare_cli':6,'prepare_wasi':6,'native_updates' :6,'native_transport_callbacks':6,'immediate_success':2,'delayed_success_after_source_shell_destruction':2,'no_reply_success_predicate_false':2,'native_future_references_released':6,'native_reply_copies_destroyed':2,'cli_canonical':6,'wasi':6,'rust_tests':sum(map(int,re.findall(r'test result: ok\. (\d+) passed',(w/'tests.stdout').read_text()))),'wasm_sha256':__import__('hashlib').sha256(wasm.read_bytes()).hexdigest()};(w/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
