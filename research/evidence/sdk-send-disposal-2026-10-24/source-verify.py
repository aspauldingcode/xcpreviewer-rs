from pathlib import Path
import sys,json,struct,hashlib,subprocess,re,tempfile
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'));from reloop.cachebind import Cache,export_names
c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');sha=lambda b:hashlib.sha256(b).hexdigest()
prior=json.loads((r/'research/evidence/service-connection-lifecycle-2026-10-24/findings.json').read_text());cancel=next(x for x in prior['operations'] if any(n['name']=='_xpc_connection_cancel' for n in x['exports']));image,base,end=c.image(int(cancel['target'],16));_,uuid=c.exports(base);assert image=='/usr/lib/system/libxpc.dylib' and uuid=='c40fcae87a173d8287cb3da4802adef1'
findings=[]
with tempfile.TemporaryDirectory(prefix='owned-send-source-') as d:
 p=Path(d);data=c.read(base,end-base)
 seg=struct.pack('<II16sQQQQiiII',0x19,152,b'__TEXT',base,len(data),4096,len(data),7,5,1,0);section=struct.pack('<16s16sQQIIIIIIII',b'__text',b'__TEXT',base+0x1000,len(data)-0x1000,4096+0x1000,2,0,0,0x80000400,0,0,0);header=struct.pack('<8I',0xfeedfacf,0x100000c,0x80000002,1,1,152,0,0);m=p/'analysis.macho';m.write_bytes((header+seg+section).ljust(4096,b'\0')+data)
 for mode,off in [('normal',0x7ecc),('cancel',0x72cc)]:
  a=base+off-4;v=struct.unpack('<I',c.read(a,4))[0];assert v>>26==37;n=v&0x3ffffff;target=a+4*(n-(1<<26) if n&(1<<25) else n);binding=c.stub(target);path,b,e=c.image(binding['target']);trie,u=c.exports(b);names=export_names(trie,binding['target']-b);assert any(x['name']=='_mach_msg_destroy' for x in names)
  lo=base+off-32;hi=base+off+16;text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(lo),'--stop-address='+hex(hi),str(m)],capture_output=True,text=True,check=True,timeout=20).stdout;words={int(a,16):int(b,16).to_bytes(4,'little') for a,b in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=c.read(lo,hi-lo);assert raw==b''.join(words[i] for i in range(lo,hi,4));findings.append({'mode':mode,'caller_return_offset':hex(off),'selected_context_bytes':hi-lo,'context_sha256':sha(raw),'callee_image':path,'callee_image_uuid':u,'callee_exports':names,'binding_profile':'bounded v5 authenticated stub','native_caller_image_uuid':uuid})
  # Raw native disassembly is retained in the calling temporary work directory,
  # never added to the published evidence bundle by this verifier.
  (w/(mode+'-caller.s')).write_text(text)
out={'caller_image':image,'caller_uuid':uuid,'selected_native_context_bytes_verified':96,'destruction_calls':findings,'scope':'Two measured libxpc callsites invoke actual mach_msg_destroy; no inference of enclosing private function ABI or full global ownership protocol.'}
f=w/'caller-findings.json'
if f.exists():assert out==json.loads(f.read_text())
else:f.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
