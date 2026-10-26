from pathlib import Path
import runpy,json,re,subprocess,contextlib,io
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):ns=runpy.run_path(str(w/'base-source-verify.py'))
m,f,word,call,binding,sha=[ns[k] for k in ['m','f','word','call','binding','sha']]
base=json.loads((w/'source-findings.json').read_text())
assert word(m,0x201f0)==0xb00006a1 and call(m,0x20200)==0x44e0
assert word(m,0x44e0)==0xaa0003e8 and word(m,0x44e4)==0xf9400020 and word(m,0x44ec)==0xd2800001
assert call(m,0x4504)==0xb26bc and binding(m,0xb26bc)=='_swift_getSingletonMetadata'
assert word(f,0xab300)==0x90000680 and word(f,0xab308)==0xd2800001
assert f.unpack('<Q',f.file_offset(0x17bf58))[0]==0x1000000000dbc0
assert f.unpack('<Q',f.file_offset(0x17bf60))[0]==0x1000000000ed44
assert f.unpack('<Q',f.file_offset(0x17bf70))[0]==0x1000000000cb8c
assert word(f,0xcb8c)==0xf9400028 and word(f,0xcb90)==0xf9000008
assert call(f,0xed44)==0xdb94 and word(f,0xdba4)==0xf9400020 and word(f,0xdba8)==0xf9000260
assert call(f,0xdbac)==0x1311e0 and binding(f,0x1311e0)=='_swift_bridgeObjectRetain'
assert word(f,0xdbc0)==0xf9400000 and call(f,0xdbc4)==0x1311c8 and binding(f,0x1311c8)=='_swift_bridgeObjectRelease'
assert call(m,0x21e34)==0xb1990 and word(m,0x21e40)==0xf9400502 and word(m,0x21e50)==0xd61f0040
ranges=[]
for p,a,b,name in [(m,0x201f0,0x20204,'box-metadata-accessor.s'),(m,0x44e0,0x4510,'metadata-accessor-common.s'),(m,0x21e20,0x21e54,'box-destroy.s'),(f,0xab300,0xab310,'plist-metadata-accessor.s'),(f,0xcb8c,0xcb98,'plist-take.s'),(f,0xed44,0xed48,'plist-copy-thunk.s'),(f,0xdb94,0xdbc8,'plist-copy-destroy.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=p.data[p.file_offset(a):p.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'image':p.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['ranges']+=ranges;base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='Owned ARM64 helper native box codec/String getter ABI/layout/ownership evidence; broader transport/UI/global resource settlement excluded';base.pop('private_box_getter_invoked',None);base['source_checks_execute_private_getter']=False;base['runtime_evidence']='Separate native.bplist and cross-runtime verification, never inferred from source checks'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(json.dumps(base))
