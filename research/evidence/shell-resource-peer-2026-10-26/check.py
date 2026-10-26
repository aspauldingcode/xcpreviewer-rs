from pathlib import Path
import subprocess,os,sys,json,plistlib,shutil,base64,struct,hashlib,resource
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;out=w/'fresh';out.mkdir(exist_ok='--resume-native' in sys.argv);capture=out/'capture';capture.mkdir(exist_ok='--resume-native' in sys.argv);resource.setrlimit(resource.RLIMIT_CORE,(0,0));b=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin');env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')};env.update(RUSTC=str(b/'rustc'),RUSTDOC=str(b/'rustdoc'))
def run(label,args,timeout=60,custom=None):
 try:p=subprocess.run(args,cwd=r,env=custom or env,capture_output=True,timeout=timeout)
 except subprocess.TimeoutExpired as e:(out/(label+'.stdout')).write_bytes(e.stdout or b'');(out/(label+'.stderr')).write_bytes(e.stderr or b'');raise
 (out/(label+'.stdout')).write_bytes(p.stdout);(out/(label+'.stderr')).write_bytes(p.stderr)
 if p.returncode:print(label,p.returncode,p.stderr.decode(errors='replace')[-1200:])
 p.check_returncode();return p.stdout
base=['--offline','--locked','--manifest-path',str(r/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(w/'target')]
# Previously captured body corpus is local-only; fresh run is verified separately.
corpus=[w/'capture/native-wire.bin',w/'capture/native-alias-wire.bin']
if all(p.exists() for p in corpus):env['XCPREVIEW_NATIVE_FD_BODIES']=':'.join(map(str,corpus))
if '--resume-native' not in sys.argv:
 run('tests',[str(b/'cargo'),'test',*base,*(['--test','xpc_descriptors','--test','native_shell_payload','--test','native_lazy_reply'] if '--replay' in sys.argv else [])])
 run('host-build',[str(b/'cargo'),'build',*base,'--bin','inspect-content-result','--bin','reencode-xpc-attachments'])
 run('wasm-build',[str(b/'cargo'),'build',*base,'--target','wasm32-wasip1','--bin','inspect-content-result'])
 cli=w/'target/debug/inspect-content-result';attachment_cli=w/'target/debug/reencode-xpc-attachments'
 for label in ['a','b']:
  source=w/('shell-'+label+'-input.bplist');data=run('reconstruct-'+label,[str(cli),'--canonical','shell-payload',str(source)],8);(out/('shell-'+label+'.bplist')).write_bytes(data)
cli=w/'target/debug/inspect-content-result';attachment_cli=w/'target/debug/reencode-xpc-attachments'
owned=env.copy();owned.update(OWNED_SHELL_A=str(out/'shell-a.bplist'),OWNED_SHELL_B=str(out/'shell-b.bplist'),OWNED_RUST_CLI=str(cli))
run('trace-build',['xcrun','clang','-Wall','-Wextra','-Werror','-dynamiclib','-lbsm',str(w/'trace.c'),'-install_name','@rpath/libtrace.dylib','-o',str(capture/'libtrace.dylib')],30)
run('metadata-build',['xcrun','clang','-fblocks',str(w/'metadata.m'),'-framework','Foundation','-o',str(capture/'metadata')],30)
metadata=json.loads(run('metadata',[str(capture/'metadata')],5));prior=json.loads((r/'research/evidence/action-xpc-2026-10-20/native-metadata.json').read_text());expected={x['selector']:x for x in prior};identities=[]
for row in metadata:
 old=expected[row['selector']];assert row['uuid']==old['uuid'] and row['image']==old['image'] and row['types']==old['types'] and row['prefix32']==old['prefix32'];identities.append({k:row[k] for k in ['selector','image','uuid','types']}|{'prefix32_sha256':hashlib.sha256(bytes.fromhex(row['prefix32'])).hexdigest()})
(out/'baseboard-identities-sanitized.json').write_text(json.dumps(identities,indent=2)+'\n')
run('oracle-build',['xcrun','clang','-Wall','-Wextra','-Werror','-Wno-error=deprecated-declarations','-fblocks',str(w/'oracle.m'),str(w/'peer.c'),'-I'+str(w),'-framework','Foundation','-lbsm','-L'+str(capture),'-ltrace','-Wl,-rpath,@executable_path','-o',str(capture/'oracle')],30)
for mode in ['native','native-alias']:
 d=capture/mode;d.mkdir();data=run(mode,[str(capture/'oracle'),mode,str(d)],8,owned);(d/'parent.json').write_bytes(data)
 child=json.loads((d/'child.json').read_text())[0];row=next(x for x in child['trace']if x['send_id']==0x20000000 and x['result']==0);raw=base64.b64decode(row['send_body']);assert struct.unpack_from('<I',raw)[0]==2;(capture/(mode+'-wire.bin')).write_bytes(raw[28:]);run(mode+'-canonical-frame',[str(attachment_cli),str(capture/(mode+'-wire.bin')),'2',str(capture/(mode+'-portable.bin')),str(capture/(mode+'-order.txt'))],8)
for mode,source,correct in [('portable','native',True),('portable-alias','native-alias',True),('wrong-order','native',False)]:
 d=capture/mode;d.mkdir();custom=owned.copy();custom['OWNED_XPC_CANDIDATE']=str(capture/(source+'-portable.bin'))
 if correct:custom['OWNED_XPC_ORDER']=str(capture/(source+'-order.txt'))
 data=run(mode,[str(capture/'oracle'),source,str(d)],8,custom);(d/'parent.json').write_bytes(data)
for mode in ['native-rust','native-rust-alias']:
 d=capture/mode;d.mkdir();data=run(mode,[str(capture/'oracle'),mode,str(d)],8,owned);(d/'parent.json').write_bytes(data)
verification=json.loads(run('peer-verification',['python3',str(w/'verify-peer.py'),str(capture)],10));(out/'peer-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
# Native typed decoder consumes every nonempty received resource, including the
# wrong-order payloads: valid shell bytes alone do not prove correct binding.
native=w/'native-shell';native.mkdir(exist_ok=True)
for name in ['native.swift','bridge.s','bridge.h','identity.c','run-native.py','source-verify.py','base-source-verify.py']:
 source=w/('native-shell-'+name)
 if source.exists():shutil.copyfile(source,native/name)
inputs=[];origins=[]
for mode in ['native','native-alias','portable','portable-alias','wrong-order','native-rust','native-rust-alias']:
 for label in ['a','b']:
  data=(capture/mode/('received-'+label+'.bplist')).read_bytes()
  if data:inputs.append({'kind':'shell-payload','input':plistlib.loads(data)});origins.append({'mode':mode,'resource':label,'bytes':len(data)})
assert len(inputs)==11;(native/'input.bplist').write_bytes(plistlib.dumps(inputs,fmt=plistlib.FMT_BINARY))
run('source',['python3',str(native/'source-verify.py')]);run('native-shell',['python3',str(native/'run-native.py')],110)
j=plistlib.loads((native/'native.bplist').read_bytes());assert all(row['accepted'] for row in j['rows']) and j['destroyedEnums']==j['destroyedPlists']==11 and j['releasedErrors']==0
for framework,uuid in [('PreviewsMessagingHost','ce1040273729381b8f0cc774e404c0ce'),('PreviewsFoundationHost','6b75229bde5d3d3794bc75af4f4704c6')]:assert [v for k,v in j['runtimeImages'].items() if '/'+framework+'.framework/' in k]==[uuid]
def normalize(v):
 import copy,unicodedata
 v=copy.deepcopy(v)
 if isinstance(v,dict):
  for k,x in v.items():
   if k in ['sourceFilePaths','linkerFlags']:x.sort(key=lambda s:unicodedata.normalize('NFD',s))
   else:v[k]=normalize(x)
 elif isinstance(v,list):v=[normalize(x) for x in v]
 return v
# These owned shells have no nonfinite values; exact typed tree comparison.
def typed(v):
 if isinstance(v,dict):return ('dictionary',tuple(sorted((k,typed(x)) for k,x in v.items())))
 if isinstance(v,list):return ('array',tuple(map(typed,v)))
 if isinstance(v,float):return ('real',struct.pack('>d',v))
 return (type(v).__name__,v)
wasm=w/'target/wasm32-wasip1/debug/inspect-content-result.wasm';results=[]
run('reparse-build',['xcrun','swiftc','-module-cache-path',str(w/'module-cache'),str(w/'reparse.swift'),'-o',str(w/'reparse')],30)
for i,(row,origin) in enumerate(zip(j['rows'],origins)):
 inp=capture/origin['mode']/('received-'+origin['resource']+'.bplist');output=out/(str(i)+'.wasi.bplist');run('wasi-'+str(i),['node',str(w/'run-wasi.cjs'),str(wasm),str(inp),str(output),'canonical','shell-payload'],10);target=normalize(row['canonical']);assert typed(plistlib.loads(output.read_bytes()))==typed(target)==typed(normalize(plistlib.loads(inp.read_bytes())))
 reparsed=out/(str(i)+'.reparsed.bplist');run('reparse-'+str(i),[str(w/'reparse'),str(output),str(reparsed)],8);assert typed(plistlib.loads(reparsed.read_bytes()))==typed(target);results.append({**origin,'native_shell_decoded':True,'wasi_and_foundation_match':True})
# Re-run native-corpus binding tests on freshly captured current native bodies.
current=env.copy();current['XCPREVIEW_NATIVE_FD_BODIES']=str(capture/'native-wire.bin')+':'+str(capture/'native-alias-wire.bin');run('fresh-corpus-tests',[str(b/'cargo'),'test',*base,'--test','xpc_descriptors','--','--nocapture'],60,current)
(out/'cross-runtime.json').write_text(json.dumps({'typed_received_payloads':11,'native_shell_accepts':11,'actual_wasi_invocations':11,'foundation_reparses':11,'cases':results},indent=2)+'\n');print(json.dumps({k:v for k,v in verification.items() if k!='cases'}));print('received typed payloads11; WASI11; reparses11')
