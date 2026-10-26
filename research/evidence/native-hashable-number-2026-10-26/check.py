from pathlib import Path
import subprocess,os,re,json,sys,plistlib,struct,datetime
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;b=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin');env=dict(os.environ,RUSTC=str(b/'rustc'),RUSTDOC=str(b/'rustdoc'))
def run(name,args,seconds=60):
 p=subprocess.run(args,cwd=r,env=env,capture_output=True,timeout=seconds);(w/(name+'.stdout')).write_bytes(p.stdout);(w/(name+'.stderr')).write_bytes(p.stderr)
 if p.returncode:print((p.stdout+p.stderr).decode()[-3000:])
 p.check_returncode();return p.stdout
run('source',['python3',str(w/'source-verify.py')])
base=['--offline','--locked','--manifest-path',str(r/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(w/'target')]
run('tests',[str(b/'cargo'),'test',*base,*(['--test','native_hashable_box'] if '--replay' in sys.argv else [])]);run('wasm-build',[str(b/'cargo'),'build',*base,'--target','wasm32-wasip1','--bin','inspect-content-result'])
assert sum(map(int,re.findall(r'test result: ok\. (\d+) passed',(w/'tests.stdout').read_text())))==(3 if '--replay' in sys.argv else 351)
run('native-harness',['python3',str(w/'run-native.py')],110)
native=plistlib.loads((w/'native.bplist').read_bytes());fixture=plistlib.loads((r/'tools/re/rust/canvas-core/tests/fixtures/native_hashable_box/native.bplist').read_bytes())
def typed(v):
 if isinstance(v,dict):return ('dictionary',tuple(sorted((k,typed(x)) for k,x in v.items())))
 if isinstance(v,list):return ('array',tuple(map(typed,v)))
 if isinstance(v,float):return ('float',struct.pack('>d',v).hex())
 return (type(v).__name__,v)
# Hash bits are randomized; only equal-pair hash-law assertions are stable.
for v in [native,fixture]:
 for p in v['pairs']:
  if p['equal']:assert p['sameHash']
  p.pop('sameHash')
assert typed(native)==typed(fixture)
for row in native['rows']:assert typed(row['input'])==typed(row['roundtrip'])
assert native['hashableBoxCount']==native['hashableBoxDestructionReturns']==96
for row in native['rows']:
 assert row['publicProjectionEqual'] and typed(row['snapshot'])==typed(row['publicProjection'])
assert len(native['pairs'])==9216
assert any('/Foundation' in name for name in native['runtimeImages'])
assert native['counts']=={'initialized':96,'encoded':96,'destroyedBoxes':192,'destroyedPropertyLists':96,'requiredCalls':0,'optionalCalls':0,'releasedErrors':0}
eq={(p['left'],p['right']):p['equal'] for p in native['pairs']};selected=list(range(96))
assert eq[26,27] and eq[26,29] and not eq[28,29]
# Derive class expectations from actual native comparisons, never from Rust keys.
def expected(indices):
 reps=[]
 for i,x in enumerate(indices):reps.append(next(j for j,y in enumerate(indices[:i+1]) if eq[x,y]))
 for i,x in enumerate(indices):
  for j,y in enumerate(indices):assert eq[x,y]==(reps[i]==reps[j])
 return {'representatives':reps,'uniqueKeys':len(set(reps))}
cases=[]
for name,indices in [('all-supported',selected),('reverse',selected[::-1]),('duplicates',selected*2),('empty',[])]+[(f'single-{i}',[i]) for i in selected]:
 cases.append({'name':name,'input':[native['rows'][i]['input'] for i in indices],'accepted':True,'output':expected(indices)})
for name,value in [('wrong-top',{}),('wrong-element',[1]),('nested-collision',[{'value':{'é':1,'e\u0301':2}}]),('nonfinite',[{'value':float('inf')}])]:cases.append({'name':name,'input':value,'accepted':False})
deep=0
for _ in range(65):deep=[deep]
cases.append({'name':'depth-profile','input':[{'value':deep}],'accepted':False})
(w/'derived-cases.bplist').write_bytes(plistlib.dumps(cases,fmt=plistlib.FMT_BINARY))
cli=w/'target/debug/inspect-content-result';wasm=w/'target/wasm32-wasip1/debug/inspect-content-result.wasm'
run('reparse-build',['xcrun','swiftc','-module-cache-path',str(w/'module-cache'),str(w/'reparse.swift'),'-o',str(w/'reparse')],30)
results=[]
for i,row in enumerate(cases):
 inp=w/(str(i)+'.input.bplist');inp.write_bytes(plistlib.dumps(row['input'],fmt=plistlib.FMT_BINARY))
 p=subprocess.run([str(cli),'--canonical','control-state-keys',str(inp)],capture_output=True,timeout=8);out=w/(str(i)+'.wasi.bplist');j=subprocess.run(['node',str(w/'run-wasi.cjs'),str(wasm),str(inp),str(out),'canonical','control-state-keys'],capture_output=True,timeout=10)
 assert (p.returncode==0)==row['accepted'] and (j.returncode==0)==row['accepted'],row['name']
 if row['accepted']:
  target=row['output'];assert typed(plistlib.loads(p.stdout))==typed(target)==typed(plistlib.loads(out.read_bytes())),row['name']
  native_out=w/(str(i)+'.native.bplist');run('reparse-'+str(i),[str(w/'reparse'),str(out),str(native_out)],8);assert typed(plistlib.loads(native_out.read_bytes()))==typed(target)
  summary=run('summary-'+str(i),[str(cli),'control-state-keys',str(inp)],8)
  summary_out=w/(str(i)+'.summary.txt');run('wasi-summary-'+str(i),['node',str(w/'run-wasi.cjs'),str(wasm),str(inp),str(summary_out),'summary','control-state-keys'],10);assert summary==summary_out.read_bytes();assert b'hello' not in summary
 else:assert p.stdout==out.read_bytes()==b''
 results.append({'case':row['name'],'accepted':row['accepted'],'complete_host_wasi_equality':True})
assert len(cases)==105 and sum(c['accepted'] for c in cases)==100
result={'native_boxes':96,'native_comparisons':9216,'typed_cached_projections':96,'public_recursive_projection_matches':96,'tool_cases':len(cases),'accepts':100,'portable_profile_rejections':5,'actual_wasi_invocations':205,'foundation_reparses':100,'cases':results}
(w/'cross-runtime.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
