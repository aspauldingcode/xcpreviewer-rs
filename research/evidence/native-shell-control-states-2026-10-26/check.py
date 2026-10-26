from pathlib import Path
import subprocess,os,re,json,sys,plistlib,struct,copy
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;b=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin');env=dict(os.environ,RUSTC=str(b/'rustc'),RUSTDOC=str(b/'rustdoc'))
def run(name,args,seconds=60):
 p=subprocess.run(args,cwd=r,env=env,capture_output=True,timeout=seconds);(w/(name+'.stdout')).write_bytes(p.stdout);(w/(name+'.stderr')).write_bytes(p.stderr)
 if p.returncode:print((p.stdout+p.stderr).decode()[-3000:])
 p.check_returncode();return p.stdout
run('source',['python3',str(w/'source-verify.py')])
base=['--offline','--locked','--manifest-path',str(r/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(w/'target')]
run('tests',[str(b/'cargo'),'test',*base,*(['--test','native_shell_control_states'] if '--replay' in sys.argv else [])]);run('wasm-build',[str(b/'cargo'),'build',*base,'--target','wasm32-wasip1','--bin','inspect-content-result'])
assert sum(map(int,re.findall(r'test result: ok\. (\d+) passed',(w/'tests.stdout').read_text())))==(3 if '--replay' in sys.argv else 358)
run('native-harness',['python3',str(w/'run-native.py')],110)
native=plistlib.loads((w/'native.bplist').read_bytes());fixture=plistlib.loads((r/'tools/re/rust/canvas-core/tests/fixtures/native_shell_control_states/native.bplist').read_bytes())
def typed(v):
 if isinstance(v,dict):return ('dictionary',tuple(sorted((k,typed(x)) for k,x in v.items())))
 if isinstance(v,list):return ('array',tuple(map(typed,v)))
 if isinstance(v,float):return ('float',struct.pack('>d',v).hex())
 return (type(v).__name__,v)
assert typed(native)==typed(fixture)
assert native['destroyedShells']==native['destroyedPlists']==13 and native['releasedShellErrors']==8
assert native['layout']=={'size':176,'stride':176,'alignment':8} and native['fieldOffsets']==[0,8,24,40,56,72,88,104,112,120,168]
cases=[]
def projection(v):
 result={'isPresent':'controlStates' in v}
 if result['isPresent']:result['controlStates']=v['controlStates']
 return result
for i,row in enumerate(native['rows']):
 case={'name':'native-shell-'+str(i),'input':row['input'],'accepted':row['accepted']}
 if row['accepted']:case['output']=projection(row['canonical'])
 cases.append(case)
for name,value in [('empty-envelope',{}),('opaque-envelope',{'uninterpreted':False}),('many-boxes',{'controlStates':[{'value':'opaque-never-print'}]*64})]:cases.append({'name':name,'input':value,'accepted':True,'output':projection(value)})
for name,value in [('wrong-top',[]),('canonical-envelope-key-collision',{'é':1,'e\u0301':2}),('canonical-box-key-collision',{'controlStates':[{'é':1,'e\u0301':2}]})]:cases.append({'name':name,'input':value,'accepted':False})
deep=0
for _ in range(65):deep=[deep]
cases.append({'name':'depth-profile','input':{'controlStates':[{'value':deep}]},'accepted':False})
(w/'derived-cases.bplist').write_bytes(plistlib.dumps(cases,fmt=plistlib.FMT_BINARY))
cli=w/'target/debug/inspect-content-result';wasm=w/'target/wasm32-wasip1/debug/inspect-content-result.wasm'
run('reparse-build',['xcrun','swiftc','-module-cache-path',str(w/'module-cache'),str(w/'reparse.swift'),'-o',str(w/'reparse')],30)
results=[]
for i,row in enumerate(cases):
 inp=w/(str(i)+'.input.bplist');inp.write_bytes(plistlib.dumps(row['input'],fmt=plistlib.FMT_BINARY))
 p=subprocess.run([str(cli),'--canonical','shell-control-states',str(inp)],capture_output=True,timeout=8);out=w/(str(i)+'.wasi.bplist');j=subprocess.run(['node',str(w/'run-wasi.cjs'),str(wasm),str(inp),str(out),'canonical','shell-control-states'],capture_output=True,timeout=10)
 assert (p.returncode==0)==row['accepted'] and (j.returncode==0)==row['accepted'],row['name']
 if row['accepted']:
  target=row['output'];assert typed(plistlib.loads(p.stdout))==typed(target)==typed(plistlib.loads(out.read_bytes())),row['name']
  native_out=w/(str(i)+'.native.bplist');run('reparse-'+str(i),[str(w/'reparse'),str(out),str(native_out)],8);assert typed(plistlib.loads(native_out.read_bytes()))==typed(target)
  summary=run('summary-'+str(i),[str(cli),'shell-control-states',str(inp)],8)
  summary_out=w/(str(i)+'.summary.txt');run('wasi-summary-'+str(i),['node',str(w/'run-wasi.cjs'),str(wasm),str(inp),str(summary_out),'summary','shell-control-states'],10);assert summary==summary_out.read_bytes() and b'opaque-never-print' not in summary and b'hello' not in summary
 else:assert p.stdout==out.read_bytes()==b''
 results.append({'case':row['name'],'accepted':row['accepted'],'complete_host_wasi_equality':True})
assert len(cases)==28 and sum(c['accepted'] for c in cases)==16
result={'native_shell_cases':21,'native_accepts':13,'native_control_states_rejections':8,'direct_shell_destruction_returns':13,'direct_property_list_destruction_returns':13,'direct_error_release_returns':8,'tool_cases':28,'accepts':16,'rejections':12,'native_matched_rejections':8,'portable_profile_or_scope_rejections':4,'actual_wasi_invocations':44,'foundation_reparses':16,'cases':results}
(w/'cross-runtime.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
