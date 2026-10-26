from pathlib import Path
import runpy,contextlib,io,json,re,subprocess
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'base-source-verify.py'))
m,f,word,call,binding,sha,fields=[n[k] for k in ['m','f','word','call','binding','sha','fields']]
assert fields(m,0xd3dac)==fields(m,0xd3dc8)==['value']
for fd in [0xd3dac,0xd3dc8]:
 t=m.relative(fd+20);assert m.data[m.file_offset(t)]==2 and binding(m,m.relative(t+1),8)=='_$ss6UInt64VMn'
assert [word(m,a) for a in range(0x24428,0x2443c,4)]==[0xf9400009,0x91000529,0xf9000009,0xf9000109,0xd65f03c0]
assert word(m,0x2445c)==0xf90007ff # initial last UInt64 zero
assert call(m,0x243d0)==0xb1c6c
assert binding(m,0xb1c6c)=='_$s22PreviewsFoundationHost26SynchronousAccessProvidingPAAE9syncWrite15defaultCallsite_qd__AA0J0V_qd__5ValueQzzYbKXEtKs8SendableRd__lF'
assert word(m,0x243a8)==0x90000001 and word(m,0x243ac)==0x9110a021 # closure address24428
assert word(m,0x5ba4)==0xf9400280 and word(m,0x1b6e0)==0xf9000100
assert call(m,0x283a4)==0x1b6e0 and call(m,0x283b0)==0x5ba4
# GroupSeed comparable implementation uses unsigned condition codes.
assert word(m,0x24594)==0xf9400008 and word(m,0x24598)==0xf9400029 and word(m,0x2459c)==0xeb09011f
base=json.loads((w/'source-findings.json').read_text());ranges=[]
for a,b,name in [(0x5ba4,0x5bac,'seed-value-getter.s'),(0x1b6e0,0x1b6e8,'seed-value-init.s'),(0x242dc,0x245e4,'seed-next-and-order.s'),(0x27d80,0x27da0,'seed-metadata.s'),(0x2839c,0x283b4,'group-seed-codec.s'),(0x283e0,0x283f4,'seed-codec-init-witness.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'image':m.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['ranges']+=ranges;base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='Typed native HostUpdateSeed/GroupSeed UInt64 conversion and value getters, full owned-process next calls, selected increment closure boundaries and unsigned group comparisons. Primitive NSNumber conversion profile runtime-qualified; full numeric bridge body not statically recovered here. No cancellation/update correlation, transport/UI/provider/global settlement.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(base['selected_source_bytes_verified'])
