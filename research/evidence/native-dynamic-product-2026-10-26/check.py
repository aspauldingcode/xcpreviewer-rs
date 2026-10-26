from pathlib import Path
import subprocess,os,re,json,sys,plistlib,struct
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;b=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin');env=dict(os.environ,RUSTC=str(b/'rustc'),RUSTDOC=str(b/'rustdoc'))
def run(name,args,seconds=60):
 p=subprocess.run(args,cwd=r,env=env,capture_output=True,timeout=seconds);(w/(name+'.stdout')).write_bytes(p.stdout);(w/(name+'.stderr')).write_bytes(p.stderr)
 if p.returncode:print((p.stdout+p.stderr).decode()[-3000:])
 p.check_returncode();return p.stdout
run('source',['python3',str(w/'source-verify.py')])
base=['--offline','--locked','--manifest-path',str(r/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(w/'target')]
run('tests',[str(b/'cargo'),'test',*base,*(['--test','native_dynamic_product'] if '--replay' in sys.argv else [])]);run('wasm-build',[str(b/'cargo'),'build',*base,'--target','wasm32-wasip1','--bin','inspect-content-result'])
assert sum(map(int,re.findall(r'test result: ok\. (\d+) passed',(w/'tests.stdout').read_text())))==(2 if '--replay' in sys.argv else 367)
run('native-harness',['python3',str(w/'run-native.py')],110)
native=plistlib.loads((w/'native.bplist').read_bytes());fixture=plistlib.loads((r/'tools/re/rust/canvas-core/tests/fixtures/native_dynamic_product/native.bplist').read_bytes())
def typed(v):
 if isinstance(v,dict):return ('dictionary',tuple(sorted((k,typed(x)) for k,x in v.items())))
 if isinstance(v,list):return ('array',tuple(map(typed,v)))
 if isinstance(v,float):return ('float',struct.pack('>d',v).hex())
 return (type(v).__name__,v)
assert typed(native)==typed(fixture)
assert native['destroyedEnums']==native['destroyedPlists']==17 and native['releasedErrors']==26
cases=native['rows']+[{'input':[],'accepted':False},{'input':{'path':'p','executablePath':'','loadingStrategy':'direct','moduleName':'m','externalFunctionBinding':'default','isRequired':float('nan')},'accepted':False}]
cli=w/'target/debug/inspect-content-result';wasm=w/'target/wasm32-wasip1/debug/inspect-content-result.wasm'
run('reparse-build',['xcrun','swiftc','-module-cache-path',str(w/'module-cache'),str(w/'reparse.swift'),'-o',str(w/'reparse')],30)
results=[]
for i,row in enumerate(cases):
 inp=w/(str(i)+'.input.bplist');inp.write_bytes(plistlib.dumps(row['input'],fmt=plistlib.FMT_BINARY));out=w/(str(i)+'.wasi.bplist')
 p=subprocess.run([str(cli),'--canonical','dynamic-product',str(inp)],capture_output=True,timeout=8);j=subprocess.run(['node',str(w/'run-wasi.cjs'),str(wasm),str(inp),str(out),'canonical','dynamic-product'],capture_output=True,timeout=10)
 assert (p.returncode==0)==row['accepted'] and (j.returncode==0)==row['accepted'],i
 if row['accepted']:
  target=row['canonical'];assert typed(plistlib.loads(p.stdout))==typed(target)==typed(plistlib.loads(out.read_bytes())),i
  native_out=w/(str(i)+'.reparsed.bplist');run('reparse-'+str(i),[str(w/'reparse'),str(out),str(native_out)],8);assert typed(plistlib.loads(native_out.read_bytes()))==typed(target)
  summary=run('summary-'+str(i),[str(cli),'dynamic-product',str(inp)],8)
  summary_out=w/(str(i)+'.summary.txt');run('wasi-summary-'+str(i),['node',str(w/'run-wasi.cjs'),str(wasm),str(inp),str(summary_out),'summary','dynamic-product'],10);assert summary==summary_out.read_bytes() and b'opaque-never-print' not in summary
 else:assert p.stdout==out.read_bytes()==b''
 results.append({'case':i,'accepted':row['accepted'],'complete_host_wasi_equality':True})
result={'native_decode_attempts':43,'native_accepts':17,'native_rejections':26,'tool_cases':45,'tool_accepts':17,'native_matched_rejections':26,'additional_profile_or_schema_rejections':2,'actual_wasi_invocations':62,'foundation_reparses':17,'cases':results}
(w/'cross-runtime.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
