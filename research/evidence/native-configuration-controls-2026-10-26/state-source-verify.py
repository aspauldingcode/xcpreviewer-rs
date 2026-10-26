from pathlib import Path
import runpy,json,re,subprocess,contextlib,io
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'predecessor-source-verify.py'))
m,f,word,call,binding,sha=[n[k] for k in ['m','f','word','call','binding','sha']]
p=type(m)(Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsPipeline.framework/Versions/A/PreviewsPipeline'))
assert sha(p.data)=='c0897c050716f12f88da4dd08c24e3d3ae1de36dc748b65ad0b7346979e40053'
assert p.uuid=='c6ed2a5e6f2e3a41a1586d2f65e00a58'
def fields(a):
 _,size,count=p.unpack('<HHI',p.file_offset(a+8));assert size==12;return [p.string(p.relative(a+16+i*size+8)) for i in range(count)]
assert fields(0x55bec8)==['states']
assert p.relative(0x55bec8+20)==p.relative(0x55be78+32)==0x54f8ea
assert word(p,0x1252a8)==0xf9000100 and word(p,0x1252ac)==0xd65f03c0
assert word(p,0x2734)==0xf9400000 and call(p,0x2738)==0x520e1c and binding(p,0x520e1c)=='_swift_bridgeObjectRelease'
assert word(p,0x461170)==0xf0000b00 and word(p,0x461174)==0x913f2000 and word(p,0x461178)==0xd2800001
assert word(p,0x460884)==0xf9000109 and call(p,0x460894)==0x41344
assert word(p,0x413d0)==0xf9400ac8 and word(p,0x413d4)==0xf9400ae9 and word(p,0x413dc)==0x54000561
assert call(p,0x41444)==0x51f8bc
assert word(p,0x4608f8)==0xf9400297 and word(p,0x4608fc)==0xf9400ae0 and word(p,0x460908)==0xf9400af9
assert call(p,0x46094c)==0x51f82c and word(p,0x460968)==0x54fffe01
assert word(p,0x460a38)==0xf9400296 and word(p,0x460a48)==0xf9400ac0 and call(p,0x460a98)==0x51f82c
assert call(p,0x3c0570)==0x41d34 and call(p,0x3c0590)==0x41344
base=json.loads((w/'source-findings.json').read_text());ranges=[]
for a,b,name in [(0x1252a8,0x1252b0,'state-init.s'),(0x461170,0x461180,'state-metadata.s'),(0x2734,0x273c,'state-destroy.s'),(0x46087c,0x460adc,'state-empty-equality-hash.s'),(0x41344,0x414b8,'state-array-equality.s'),(0x3c051c,0x3c05c4,'runnable-configuration-id-equality.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=p.data[p.file_offset(a):p.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'image':p.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['source_images'][p.path.name]={'sha256':sha(p.data),'uuid':p.uuid};base['ranges']+=ranges;base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='CanvasControlState ordered storage/copy/equality/hash ABI and source-only Configuration.ID delegation. Actual container calls in native.bplist; full request identity/installation/transport/UI/provider/global settlement excluded.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(json.dumps({'bytes':base['selected_source_bytes_verified'],'pipeline_pin':base['source_images'][p.path.name]}))
