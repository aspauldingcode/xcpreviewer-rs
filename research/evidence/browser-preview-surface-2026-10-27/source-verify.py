from pathlib import Path
import sys,json,hashlib,re,subprocess
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
base=Path('/Applications/Xcode.app/Contents/SharedFrameworks');m=MachO(base/'PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost');f=MachO(base/'PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost');sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(m.data)=='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c';assert sha(f.data)=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
symbols=subprocess.run(['xcrun','nm',str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode()
for offset,name in [(0x9a6c8,'$s21PreviewsMessagingHost13RenderPayloadVMa'),(0x8d9a0,'$s21PreviewsMessagingHost13RenderPayloadV17propertyListValueAC0a10FoundationC008PropertyG0V_tKcfC'),(0x8d740,'$s21PreviewsMessagingHost13RenderPayloadV17propertyListValue0a10FoundationC008PropertyG0Vvg')]:assert f'{offset:016x} T _{name}' in symbols
s,ind,libs=tables(m)
def binding(a):
 sec=next(t for t in m.sections if t['address']<=a<t['address']+t['size']);i=index(m,sec,a,12,ind);n,k,ss,d,v=m.unpack('<IBBHQ',s[0]+16*i);o=s[2]+n;return m.data[o:m.data.index(0,o)].decode()
# Record only imported symbols reached from selected public decoder regions.
ranges=[];imports=set()
for a,b,label in [(0x4aaf4,0x4b4c4,'bitmap-codec'),(0x4bb70,0x4c240,'region-codec'),(0x8d740,0x8dda0,'render-codec')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,check=True,timeout=20).stdout.decode();(w/(label+'.s')).write_text(text)
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4))
 for pc in range(a,b,4):
  v=m.u32(m.file_offset(pc))
  if v>>26 not in [5,37]:continue
  n=v&0x3ffffff;target=pc+4*(n-(1<<26) if n&(1<<25) else n)
  if any(t['address']<=target<t['address']+t['size'] and t['flags']&255==8 for t in m.sections):imports.add(binding(target))
 ranges.append({'label':label,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
assert any('PropertyListV' in s for s in imports)
out={'source_images':{'PreviewsMessagingHost':{'sha256':sha(m.data),'uuid':m.uuid},'PreviewsFoundationHost':{'sha256':sha(f.data),'uuid':f.uuid}},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'decoder_imports':sorted(imports),'scope':'Selected native RenderPayload/BitmapDescription/SelectableRegion encoder/decoder source regions independently compared; runtime independently measures metadata104/104/8 offsets0/80/88/96 and numeric outcomes. No native CGImage drawing, surfaces, provider application or Canvas UI claimed.'};(w/'source-findings.json').write_text(json.dumps(out,indent=2)+'\n');print('Verified',out['source_bytes_verified'],'render codec bytes')
