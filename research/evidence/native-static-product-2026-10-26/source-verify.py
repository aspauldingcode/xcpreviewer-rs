from pathlib import Path
import runpy,contextlib,io,json,re,subprocess
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'base-source-verify.py'))
m,f,word,call,binding,sha,fields=[n[k] for k in ['m','f','word','call','binding','sha','fields']]
assert fields(m,0xd3730)==fields(m,0xd3764)==['productIdentity','seed','builtTargetDescriptions']
assert [call(m,a) for a in [0x19ed0,0x19f30,0x19f8c]]==[0xb1948]*3
assert word(m,0x19e94)==0xaa0803f6 and word(m,0x19d34)==0xa9404e9b # indirect result/self
assert word(m,0x19ff8)==0xf9441929 and binding(m,0xe4830,8)=='__swiftEmptyArrayStorage'
assert word(m,0x1a000)==0x9a880138 # missing array -> empty
assert word(m,0x19d5c)==0xb4000253 and word(m,0x19da4)==0x7100071f and word(m,0x19da8)==0x54000240 and word(m,0x19df4)==0xb40002c8
assert word(m,0x1a338)==0xf9400400 and word(m,0x1a340)==0xf9401660
assert call(m,0x1a33c)==call(m,0x1a34c)==0xb2548
base=json.loads((w/'source-findings.json').read_text())
for a,b,name in [(0x19d10,0x1a040,'static-product-codec.s'),(0x1a328,0x1a350,'static-product-destroy.s'),(0x1a4f8,0x1a508,'static-product-metadata.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);base['ranges'].append({'image':m.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='Complete static product wire record with optional identity/seed, default-empty ordered target array, canonical omission and actual composed native target array validation. Two inherited nested Set wire orders excluded. No native constructor/reuse/link/load policy, incremental/setup/shell, transport/UI/provider or final resource settlement.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(base['selected_source_bytes_verified'])
