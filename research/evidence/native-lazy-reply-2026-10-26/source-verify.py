from pathlib import Path
import runpy,contextlib,io,json,re,subprocess
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'base-source-verify.py'))
m,f,word,call,binding,sha,fields=[n[k] for k in ['m','f','word','call','binding','sha','fields']]
assert fields(m,0xd5884)==['deserialized','serialized']
assert word(m,0x6e9b4)==0xaa1403f6 and word(m,0x6e9b8)==0xaa0803f7
assert call(m,0x6ea60)==0xb2a00 # ObjC selector stub; not a12-byte symbol stub
assert m.string(m.unpack('<Q',m.file_offset(0xf4718))[0]&0xfffffffff)=='propertyListWithData:options:format:error:'
assert binding(m,0xe42c8,8)=='_objc_msgSend'
assert call(m,0x6ead4)==0xb25e4 and binding(m,0xb25e4)=='_swift_dynamicCast'
assert [word(m,a) for a in [0x6ea4,0x6ea8,0x6eac]]==[0xaa0103e8,0xaa0203e1,0xaa0803e2]
assert word(m,0x6ecb8)==0x7100041f and word(m,0x6ecbc)==0x54000061
assert word(m,0x6efac)==0x7100041f and call(m,0x6efc0)==0x47080
base=json.loads((w/'source-findings.json').read_text())
for a,b,name in [(0x6e960,0x6ebfc,'lazy-plist.s'),(0x6ebfc,0x6edf8,'lazy-data.s'),(0x6ef98,0x6f078,'lazy-copy-destroy.s'),(0x6ea0,0x6eb4,'lazy-enum-tag.s'),(0xb2a00,0xb2a20,'lazy-objc-parse-stub.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);base['ranges'].append({'image':m.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='Actual LazyPropertyList enum copy/destruction, dictionary/data getters, serialized Foundation parsing and dictionary cast, returned Data ownership with one owned no-copy buffer. No transport callback, kernel rights, delivery or provider settlement.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(base['selected_source_bytes_verified'])
