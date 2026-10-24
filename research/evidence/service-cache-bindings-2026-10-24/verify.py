from pathlib import Path
import sys,json,struct,re,subprocess,hashlib
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache,export_names
import tempfile
work=tempfile.TemporaryDirectory(prefix='service-cache-verify-');w=Path(work.name);c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;data=c.read(base,0x10440);assert hashlib.sha256(data).hexdigest()=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
seg=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',base,len(data),4096,len(data),7,5,1,0)
section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',base+0x16f8,45500+2272,4096+0x16f8,2,0,0,0x80000400,0,0,0)
header=struct.pack('<8I',0xfeedfacf,0x100000c,0x80000002,1,1,152,0,0)
p=w/'services-analysis.macho';p.write_bytes((header+seg+section).ljust(4096,b'\0')+data)
regions=[(0x4e30,0x50a4),(0x50a4,0x53e0),(0x53e0,0x5ddc),(0x3d00,0x3d60),(0x8e28,0x8e34)];calls={};bodies=[]
for a,b in regions:
 x=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(p)],capture_output=True,text=True,check=True,timeout=20);(w/('source-'+hex(a)+'.s')).write_text(x.stdout)
 words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',x.stdout,re.M)};assert b''.join(words[i] for i in range(base+a,base+b,4))==data[a:b];bodies.append({'offset':hex(a),'bytes':b-a,'sha256':hashlib.sha256(data[a:b]).hexdigest()})
 for site in range(a,b,4):
  v=struct.unpack_from('<I',data,site)[0]
  if v>>26 in [5,0x25]:
   off=v&0x3ffffff;target=base+site+4*(off-(1<<26) if off&(1<<25) else off)
   if base+0xc8b4<=target<base+0xd194:calls.setdefault(target,[]).append(hex(base+site))
bindings=[];cache={}
for stub,sites in sorted(calls.items()):
 row=c.stub(stub);path,b,end=c.image(row['target'])
 if b not in cache:cache[b]=c.exports(b)
 raw,uuid=cache[b];names=export_names(raw,row['target']-b);row.update(target=hex(row['target']),image=path,image_uuid=uuid,exports=names,call_sites=sites);row.pop('raw_word');bindings.append(row)
# Independently verify selected authenticated stub instruction bytes through LLVM.
minimum=min(calls);maximum=max(calls)+16
text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(minimum),'--stop-address='+hex(maximum),str(p)],capture_output=True,text=True,check=True,timeout=20).stdout
(w/'authenticated-stubs.s').write_text(text)
words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)}
for stub in calls:assert b''.join(words[i] for i in range(stub,stub+16,4))==data[stub-base:stub-base+16]
by_name={name['name']:b for b in bindings for name in b['exports']}
assert struct.unpack_from('<I',data,0x5384)[0]==0xd2800002
assert struct.unpack_from('<I',data,0x5508)[0]==0x54001440
assert struct.unpack_from('<I',data,0x5300)[0]==0x9138a210
assert struct.unpack_from('<I',data,0x5340)[0]==0x91340210
assert struct.unpack_from('<I',data,0x8e30)[0]==0x17fff16c
assert by_name['_xpc_connection_send_message']['call_sites']==['0x263305058']
assert by_name['_xpc_connection_send_message_with_reply']['call_sites']==['0x26330538c']
assert by_name['_xpc_get_type']['call_sites']==['0x2633054f4']
assert by_name['_$s3XPC0A16_TYPE_DICTIONARYs13OpaquePointerVvg']['call_sites']==['0x2633054fc']
# A broken real chain must not yield any binding; mutate only an owned copy.
from reloop.cachebind import v5_code_pointer
row=by_name['_xpc_connection_send_message_with_reply'];page=bytearray(c.read(int(row['page_origin'],16),row['page_size']));first=row['page_start'];start=first*8
word=struct.unpack_from('<Q',page,start)[0];struct.pack_into('<Q',page,start,word&~(2047<<52))
try:v5_code_pointer(page,first,int(row['slot'],16)-int(row['page_origin'],16),int(row['value_add'],16))
except ValueError:chain_fault_rejected=True
else:raise AssertionError('Broken chain accepted')
assert chain_fault_rejected
# Independent Apple-tool export decoder confirms libxpc exact target names.
x=subprocess.run(['xcrun','dyld_info','-exports','/usr/lib/system/libxpc.dylib'],capture_output=True,text=True,check=True,timeout=20);(w/'libxpc-exports.txt').write_text(x.stdout)
for name in ['_xpc_connection_send_message','_xpc_connection_send_message_with_reply']:
 row=by_name[name];target=int(row['target'],16);_,imagebase,_=c.image(target)
 matches=re.findall(r'^\s*0x([0-9A-Fa-f]+)\s+'+re.escape(name)+r'\s*$',x.stdout,re.M);assert len(matches)==1 and int(matches[0],16)==target-imagebase
print('Resolved',len(bindings),'authenticated stubs; corrupted real chain rejected; Apple export decoder agrees')
out={'services_text_sha256':hashlib.sha256(data).hexdigest(),'source_only':True,'private_functions_invoked':False,'pac_signing_or_bypass':False,'live_ipc_observed':False,'target_settlement_proven':False,'bindings':bindings,'selected_ranges':bodies,'selected_source_bytes_verified':sum(x['bytes'] for x in bodies)+16*len(bindings),'stub_instruction_bytes_verified':16*len(bindings),'corrupted_real_chain_rejected':True,'libxpc_exports_independently_confirmed':True,'cache_reads':list(c.reads.values())};expected=json.loads(Path(__file__).with_name('findings.json').read_text());assert out==expected;print(json.dumps({'verified':True,'bindings':len(bindings),'source_bytes':out['selected_source_bytes_verified'],'corrupted_real_chain_rejected':True},indent=2));work.cleanup()
