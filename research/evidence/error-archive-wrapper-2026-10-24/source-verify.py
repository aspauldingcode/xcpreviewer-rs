from pathlib import Path
import sys,json,hashlib,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'));from reloop.swiftmeta import MachO
m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(m.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
def word(a):return m.u32(m.file_offset(a))
def call(a):
 v=word(a);assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
def conditional(a,target):
 v=word(a);n=(v>>5)&0x7ffff;assert a+4*(n-(1<<19) if n&(1<<18) else n)==target
fd=m.relative(0x151d30+16);kind,size,n=m.unpack('<HHI',m.file_offset(fd+8));assert kind==2 and size==12 and n==2;cases=[m.string(m.relative(fd+16+i*size+8)) for i in range(n)];assert cases==['main','cause']
def literal(addresses):
 value=0
 for i,a in enumerate(addresses):
  v=word(a);imm=(v>>5)&65535;shift=((v>>21)&3)*16
  assert (v&0x7f800000)==(0x52800000 if i==0 else 0x72800000)
  value=(value&~(65535<<shift))|(imm<<shift)
 return value.to_bytes(8,'little')
main=literal([0x5e3b4,0x5e3b8])[:4].decode();underlying=(literal([0x5e3bc,0x5e3c0,0x5e3c4,0x5e3c8])+literal([0x5e3d4,0x5e3d8]))[:10].decode();assert (main,underlying)==('main','underlying');assert word(0x5e3b0)==0x7100051f
for a,t in [(0x5e678,0x5ead0),(0x5e6ac,0x5ead0),(0x5e710,0x5f154),(0x5e734,0x5f154),(0x5eb90,0x61ad8),(0x5e5e8,0xac550),(0x5f218,0x5e634)]:assert call(a)==t
for a,t in [(0x5e680,0x5e6c0),(0x5e6b4,0x5e6ec),(0x5e720,0x5e748),(0x5e73c,0x5e754)]:conditional(a,t)
# Storage: main existential at0, underlying at0x28; projection delegates only
# to one branch. Verify exact loads and witness offsets before indirect call.
assert word(0x5f8d8)==0x9100a280 and word(0x5f8d4)==0xa9445693 and word(0x5f8e4)==0xf94032a8 and word(0x5f8f4)==0xd63f0100
assert word(0x5f94c)==0xa941d693 and word(0x5f958)==0xf94042a8 and word(0x5f968)==0xd63f0100
ranges=[]
for a,b in [(0x5e370,0x5e798),(0x5ead0,0x5ec34),(0x61ad8,0x61c60),(0x5f8c4,0x5f980),(0x5f154,0x5f2f4)]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(m.data),'uuid':m.uuid,'reflected_cases':cases,'wire_keys':[main,underlying],'required_dictionary_order':['main','underlying'],'recursive_decode_order':['main','underlying'],'potential_crash_branch':'underlying','native_flag_branch':'main','native_private_runtime_invoked':False,'portable_limits_native_parity':False,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges)}
p=Path(__file__).parent/'source-findings.json'
if p.exists():assert out==json.loads(p.read_text())
else:p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
