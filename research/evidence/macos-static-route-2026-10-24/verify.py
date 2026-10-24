"""Pinned offline static selector and import/consumer verification."""
from pathlib import Path
import json,sys,hashlib,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
from reloop.discriminants import pc_relative
p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsDeveloperTools.framework/Versions/A/PreviewsDeveloperTools');m=MachO(p);pin='d70f346fc8c8f7085f0a8b05fe160776b5464a3a6efc146259076fd12aa21cc2';assert hashlib.sha256(m.data).hexdigest()==pin
names=['platform','dyldPlatform','previewKitRelativePath','previewKitAbsoluteURL','frameworkModeAgentRelativePath','staticRenderingMethod','serviceVariant'];a=0xb485c
assert m.unpack('<HHI',m.file_offset(a+8))==(0,12,7);assert [m.string(m.relative(a+16+12*i+8)) for i in range(7)]==names
assert m.u32(m.file_offset(0xae4cc+20))==7;vector=m.u32(m.file_offset(0xae4cc+24));assert vector==2 and vector*8+5*4==0x24
symbolic=m.relative(a+16+5*12+4);assert symbolic==0xb0732;off=m.file_offset(symbolic);assert m.data[off]==1;assert symbolic+1+m.unpack('<i',off+1)[0]==0xae4b0
assert m.unpack('<HHI',m.file_offset(0xb4834+8))==(2,12,2);assert [m.string(m.relative(0xb4834+16+12*i+8)) for i in range(2)]==['layerHost','ioSurface']
sym,ind,libs=tables(m);ptr=next(s for s in m.sections if s['address']<=0xc5a30<s['address']+s['size']);bindings=[]
for addr,fragment in [(0xc5a30,'AgentMessageTypeO05layerC0'),(0xc5a38,'AgentMessageTypeO16captureIOSurface')]:
 i=index(m,ptr,addr,8,ind);nameoff,kind,section,desc,value=m.unpack('<IBBHQ',sym[0]+16*i);assert kind&0xe==0 and section==0 and value==0;o=sym[2]+nameoff;end=m.data.find(b'\0',o);name=m.data[o:end].decode();assert fragment in name and name.endswith('yA2CmFWC');lib=libs[(desc>>8)-1];assert lib=='@rpath/SharedFrameworks/PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost';bindings.append({'pointer':hex(addr),'symbol':name,'library':lib})
for a,expected in [(0x2582c,0x7100011f),(0x25830,0x9a8a0128),(0x25834,0xb9400101),(0x28428,0x7100011f),(0x2842c,0x9a8b0128),(0x28430,0xb9400101),(0x2ae04,0xb9802408),(0x2ae08,0x38686a88),(0x2ae14,0x340002e8)]:assert m.u32(m.file_offset(a))==expected
# Independent A64 branch sign extension for exact declared static constructors.
for site,target in [(0x2ae00,0x20fa8),(0x2ae54,0x34208),(0x2aeac,0xc458)]:
 word=m.u32(m.file_offset(site));assert word>>26==0x25;delta=word&0x3ffffff;delta=delta-(1<<26) if delta&(1<<25) else delta;assert site+delta*4==target
regions=[(0x25810,0x2584c),(0x28404,0x28440),(0x2addc,0x2aed0)];bodies=[]
for a,b in regions:
 out=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout.decode()
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',out,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert b''.join(words[x] for x in range(a,b,4))==raw;bodies.append({'start':hex(a),'bytes':b-a,'sha256':hashlib.sha256(raw).hexdigest()})
result={'target_sha256':pin,'uuid':m.uuid,'field':'LocalMacPlatformSupport.staticRenderingMethod','field_index':5,'metadata_field_offset_slot':'0x24','case_names':['layerHost','ioSurface'],'request_import_bindings':bindings,'request_selection':'zero selects layerHost, nonzero selects captureIOSurface; request-side metadata type provenance not fully traced','static_consumer':'Field is independently bound to staticRenderingMethod; zero selects MacOSLayerHostedPreviewViewable.create at0xc458, nonzero IOSurfacePreviewViewable.create at0x34208','selected_ranges':bodies,'selected_bytes_verified':sum(x['bytes'] for x in bodies),'source_only':True,'native_execution':False,'frame_association':False,'completion_semantics':False}
print(json.dumps(result,indent=2))
