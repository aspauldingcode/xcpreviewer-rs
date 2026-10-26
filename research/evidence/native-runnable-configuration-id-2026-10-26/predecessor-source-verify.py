from pathlib import Path
import runpy,json,re,subprocess,contextlib,io
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):ns=runpy.run_path(str(w/'prior-source-verify.py'))
m,f,word,call,binding,sha=[ns[k] for k in ['m','f','word','call','binding','sha']]
base=json.loads((w/'source-findings.json').read_text())
assert ns['ns']['fields'](f,0x159c44)==['value','hashable']
assert call(f,0xa99c4)==0x97d00 and call(f,0xa99dc)==0xab118 and call(f,0xa99ec)==0xa9a20
assert word(f,0xa99a0)==0xf9400b28 and word(f,0xa99f0)==0xf9400728
assert word(f,0xa9b54)==0xb9802408 and call(f,0xa9b68)==0x130730
assert binding(f,0x130730)=='_$ss11AnyHashableV2eeoiySbAB_ABtFZ'
assert call(f,0xa9b80)==call(f,0xa9bbc)==0x13073c
assert binding(f,0x13073c)=='_$ss11AnyHashableV4hash4intoys6HasherVz_tF'
assert call(f,0xa9c9c)==0xa9970 and word(f,0xa9c78)==0xf9400988
assert word(f,0x64338)==0xf9400802 and word(f,0x64340)==0xf9400923
assert word(f,0xab464)==0xf9400821 and word(f,0xab470)==0xd63f0100 and call(f,0xab484)==0x4474
assert call(f,0xab120)==0xd2dc and call(f,0xd2f8)==0x131324 and binding(f,0x131324)=='_swift_getGenericMetadata'
assert call(m,0x20374)==0xb2710 and binding(m,0xb2710)=='_swift_getWitnessTable'
assert binding(f,0x1716e0,8)=='_$ss11AnyHashableVN'
ranges=[]
for p,a,b,name in [(f,0xa9970,0xaa26c,'hashable-box-methods.s'),(f,0x64334,0x6434c,'hashable-value-getter.s'),(f,0xab454,0xab494,'hashable-destroy.s'),(f,0xab118,0xab124,'hashable-metadata.s'),(f,0xd2dc,0xd30c,'generic-metadata-common.s'),(m,0x20348,0x20388,'conformance-accessor.s'),(m,0x241bc,0x241d8,'conformance-call-site.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=p.data[p.file_offset(a):p.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'image':p.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['ranges']+=ranges;base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='Actual owned HashableBox<PlistValueBox> methods and bounded portable equality profile. Source evidence distinct from runtime. Wider NSNumber boundary conversion, generic identity, UI/transport/global settlement remain open.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(json.dumps({'bytes':base['selected_source_bytes_verified'],'pins':base['source_images']}))
