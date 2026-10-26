from pathlib import Path
import subprocess,os,re,json,sys,plistlib,struct,copy,unicodedata
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;b=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin');env=dict(os.environ,RUSTC=str(b/'rustc'),RUSTDOC=str(b/'rustdoc'))
def run(name,args,seconds=60):
 p=subprocess.run(args,cwd=r,env=env,capture_output=True,timeout=seconds);(w/(name+'.stdout')).write_bytes(p.stdout);(w/(name+'.stderr')).write_bytes(p.stderr)
 if p.returncode:print((p.stdout+p.stderr).decode()[-3000:])
 p.check_returncode();return p.stdout
run('source',['python3',str(w/'source-verify.py')])
base=['--offline','--locked','--manifest-path',str(r/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(w/'target')]
run('tests',[str(b/'cargo'),'test',*base,*(['--test','native_lazy_reply'] if '--replay' in sys.argv else [])]);run('wasm-build',[str(b/'cargo'),'build',*base,'--target','wasm32-wasip1','--bin','inspect-content-result'])
assert sum(map(int,re.findall(r'test result: ok\. (\d+) passed',(w/'tests.stdout').read_text())))==(2 if '--replay' in sys.argv else 389)
run('native-harness',['python3',str(w/'run-native.py')],110)

native=plistlib.loads((w/'native.bplist').read_bytes());fixture=plistlib.loads((r/'tools/re/rust/canvas-core/tests/fixtures/native_lazy_reply/native.bplist').read_bytes());inputs=plistlib.loads((w/'input.bplist').read_bytes())
def typed(v):
 if isinstance(v,dict):return ('dictionary',tuple(sorted((k,typed(x)) for k,x in v.items())))
 if isinstance(v,list):return ('array',tuple(map(typed,v)))
 if isinstance(v,float):return ('float',struct.pack('>d',v).hex())
 return (type(v).__name__,v)
def canonical(value):
 import copy,unicodedata
 value=copy.deepcopy(value)
 if isinstance(value,dict):
  for k,v in value.items():
   if k in ['sourceFilePaths','linkerFlags']:v.sort(key=lambda s:unicodedata.normalize('NFD',s))
   else:value[k]=canonical(v)
 elif isinstance(value,list):value=[canonical(v) for v in value]
 return value
assert native['layouts']==fixture['layouts'] and native['destroyedEnums']==38 and native['destroyedPlists']==18 and native['releasedErrors']==20
assert native['rows'][-1]==fixture['rows'][-1] and native['rows'][-1]['finalCustomDeallocatorCalls']==1
cases=[]
for i,(row,prior,item) in enumerate(zip(native['rows'],fixture['rows'],inputs)):
 assert row['accepted']==prior['accepted'] and row['errorReturns']==prior['errorReturns'] and row['sourceDestroyedBeforeRead'] and not row['dataError']
 assert typed(row['decoded'])==typed(prior['decoded'])
 if item['kind']=='serialized':assert row['data']==item['bytes']==prior['data']
 else:assert typed(plistlib.loads(row['data']))==typed(item['dictionary'])
 if row['accepted']:
  assert len(row['decoded'])==2 and typed(row['decoded'][0])==typed(row['decoded'][1])
  if 'setupPayload' in row['decoded'][0]:cases.append(row)
assert len(cases)==4
cli=w/'target/debug/inspect-content-result';wasm=w/'target/wasm32-wasip1/debug/inspect-content-result.wasm'
run('reparse-build',['xcrun','swiftc','-module-cache-path',str(w/'module-cache'),str(w/'reparse.swift'),'-o',str(w/'reparse')],30)
for i,row in enumerate(cases):
 inp=w/(str(i)+'.input.bplist');inp.write_bytes(row['data']);out=w/(str(i)+'.wasi.bplist')
 p=run('host-canonical-'+str(i),[str(cli),'--canonical','shell-payload',str(inp)],8)
 run('wasi-canonical-'+str(i),['node',str(w/'run-wasi.cjs'),str(wasm),str(inp),str(out),'canonical','shell-payload'],10)
 target=canonical(row['decoded'][0]);assert typed(plistlib.loads(p))==typed(target)==typed(plistlib.loads(out.read_bytes()))
 reparsed=w/(str(i)+'.reparsed.bplist');run('reparse-'+str(i),[str(w/'reparse'),str(out),str(reparsed)],8);assert typed(plistlib.loads(reparsed.read_bytes()))==typed(target)
 summary=run('host-summary-'+str(i),[str(cli),'shell-payload',str(inp)],8);summary_out=w/(str(i)+'.summary.txt');run('wasi-summary-'+str(i),['node',str(w/'run-wasi.cjs'),str(wasm),str(inp),str(summary_out),'summary','shell-payload'],10);assert summary==summary_out.read_bytes() and b'opaque-never-print' not in summary
results={'native_lazy_cases':19,'native_dictionary_getter_calls':38,'native_dictionary_success_returns':18,'native_dictionary_error_returns':20,'native_case_data_getter_returns':19,'binary_profile_cases':17,'native_xml_cases':2,'native_xml_dictionary_accepts':1,'actual_wasi_invocations':8,'foundation_reparses':4,'typed_shell_compositions':4,'owned_buffer_bytes':8192,'owned_buffer_final_custom_deallocator_calls':1,'additional_lifetime_data_getter_returns':1,'fixture_enum_destruction_returns':38,'additional_lifetime_enum_destruction_returns':2}
(w/'cross-runtime.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
