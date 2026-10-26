from pathlib import Path
import runpy,contextlib,io,json,re,subprocess
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'base-source-verify.py'))
m,f,word,call,binding,sha,fields=[n[k] for k in ['m','f','word','call','binding','sha','fields']]
expected=['installName','isExecutable','buildableName','moduleName','mergedModuleNames','platformVersion','objectFiles','staticArchives','rpaths','loadCommands','architectures','enforceWeakSymbolPaths','linkerFlags','opaqueTypeErasureEnabled','output','diagnosticInfo','additionalArtifactPaths']
assert fields(m,0xd3334)==expected
keys=['installName','isExecutable','buildableName','moduleName','platformVersion','objectFiles','staticArchives','rpaths','loadCommands','enforceWeakSymbolPaths','architectures','linkerFlags','opaqueTypeErasureEnabled','output','diagnosticInfo','additionalArtifactPaths']
assert fields(m,0xd34d4)==keys and 'mergedModuleNames' not in keys
assert fields(m,0xd34ac)==['allLoad','objC']
for i,t in {0:'SS',1:'Sb',2:'SSSg',3:'SSSg',4:'SaySSG',8:'SaySSG',10:'SaySSG',11:'Sb',13:'Sb',14:'SSSg',15:'SaySSG',16:'SaySSG'}.items():assert m.string(m.relative(0xd3334+20+12*i))==t
assert call(m,0x94a4)==0xb190c
optional_calls=[0x9504,0x9544,0x95d8,0x964c,0x9710,0x97c8,0x988c,0x9954,0x99ec,0x9a74,0x9b28,0x9bd0,0x9c1c,0x9cd0,0x9d74]
assert [call(m,a) for a in optional_calls]==[0xb1948]*15
assert word(m,0x9468)==0xaa0803fa and word(m,0x8d94)==0xaa1403e9 # indirect result/self
assert word(m,0x9e98)==0xa903af5c # native mergedModuleNames field at56 receives empty array
assert word(m,0x9e20)==0xf9441b9c and binding(m,0xe4830,8)=='__swiftEmptyArrayStorage'
assert [word(m,a) for a in [0x9e44,0x9e48,0x9e68,0x9e6c]]==[0xb940c7e8,0x12000114,0xb9403fe8,0x12000108]
assert [word(m,a) for a in [0x9be4,0x9be8,0x9bec,0x9e08,0x9e70]]==[0x394343f8,0x71000b1f,0x1a9f17e8,0x2a180118,0x12000309]
base=json.loads((w/'source-findings.json').read_text())
for a,b,name in [(0x8d78,0x9440,'target-encode.s'),(0x9440,0x9eec,'target-decode.s'),(0x1381c,0x138b8,'target-destroy.s'),(0x13f40,0x13f50,'target-metadata.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);base['ranges'].append({'image':m.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='Complete built-target wire codec:17 native fields/16 wire keys, only installName required, optional/defaulted nested values, omission policies, native merged-module field initialized empty/excluded from wire, actual owned field-mutation encoding control. Array order preserved; linker/source-path Set wire order deliberately not reproduced. No constructor route, linker flag effects, architecture/reuse policy, actual file loading, static/setup/shell, transport/UI/provider or final resource settlement.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(base['selected_source_bytes_verified'])
