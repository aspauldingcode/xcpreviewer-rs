"""Capture one own-process runtime image for local RE. Never publish outputs.

The executable may run library initializers via dlopen; resolved entrypoints are
never called. Live rebased data and omitted LINKEDIT make this an analysis view,
not a standalone/original binary. Use only a fresh directory beneath research/raw
or /private/tmp. No system protections or existing target process are modified.
"""
from pathlib import Path
import os,sys,json,struct,hashlib,subprocess
root=Path('/Users/8amps/xcpreviewer-rs');source=Path(__file__).resolve().parent
output=Path(sys.argv[1]).resolve()
assert str(output).startswith(str(root/'research/raw')+'/') or str(output).startswith('/private/tmp/')
sys.path.insert(0,str(root/'tools/re'))
from reloop.core import Controller
with Controller().lock():
 output.mkdir(parents=True,exist_ok=False)
 clang='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang'
 p=subprocess.run([clang,'-Wall','-Wextra','-Werror',str(source/'map_image.c'),'-lobjc','-o',str(output/'map_image')],capture_output=True,timeout=30);(output/'build.log').write_bytes(p.stdout+p.stderr);p.check_returncode()
 p=subprocess.run([str(output/'map_image'),str(output)],capture_output=True,timeout=15);(output/'run.log').write_bytes(p.stdout+p.stderr);p.check_returncode()
 m=json.loads((output/'mapped.json').read_text());assert m['cpu']==0x100000c and 0<len(m['segments'])<=32 and m['bytes']<=64*1024*1024
 segments=m['segments'];ph=[];sections=[];payload=bytearray(4096);offset=4096;strings=bytearray(b'\0')
 for s in segments:
  b=(output/s['file']).read_bytes();assert len(b)==s['size'];address=int(s['address'],16);prot=s['protection'];flags=(4 if prot&1 else 0)|(2 if prot&2 else 0)|(1 if prot&4 else 0)
  ph.append(struct.pack('<IIQQQQQQ',1,flags,offset,address,address,len(b),len(b),1))
  name=len(strings);strings.extend(s['name'].encode('ascii')+b'\0');sections.append(struct.pack('<IIQQQQIIQQ',name,1,2|(1 if prot&2 else 0)|(4 if prot&4 else 0),address,offset,len(b),0,0,1,0))
  payload.extend(b);offset+=len(b);pad=(-offset)%4096;payload.extend(bytes(pad));offset+=pad
 strname=len(strings);strings.extend(b'.shstrtab\0');strstart=len(payload);payload.extend(strings);payload.extend(bytes((-len(payload))%8));shoff=len(payload)
 payload.extend(bytes(64));payload.extend(b''.join(sections));payload.extend(struct.pack('<IIQQQQIIQQ',strname,3,0,0,strstart,len(strings),0,0,1,0))
 ident=b'\x7fELF'+bytes([2,1,1,0])+bytes(8);payload[:64]=struct.pack('<16sHHIQQQIHHHHHH',ident,3,183,1,0,64,shoff,0,64,56,len(ph),64,len(sections)+2,len(sections)+1);payload[64:64+56*len(ph)]=b''.join(ph)
 elf=output/'libxpc-mapped-v2.elf';elf.write_bytes(payload)
 # Independent binding: dlsym's direct32-byte probe equals the enclosing segment
 # bytes; ELF program headers then map that exact same prefix at the same VA.
 bindings=[]
 for i,symbol in enumerate(m['symbols']):
  address=int(symbol['address'],16);assert address
  candidates=[s for s in segments if int(s['address'],16)<=address and address+32<=int(s['address'],16)+s['size']];assert len(candidates)==1 and candidates[0]['protection']&4
  s=candidates[0];n=segments.index(s);start=address-int(s['address'],16);b=(output/s['file']).read_bytes()[start:start+32];assert b==(output/('symbol-%d.bin'%i)).read_bytes()
  fileoff=struct.unpack_from('<Q',payload,64+n*56+8)[0];assert payload[fileoff+start:fileoff+start+32]==b
  objdump='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/llvm-objdump'
  p=subprocess.run([objdump,'--disassemble','--start-address='+hex(address),'--stop-address='+hex(address+32),str(elf)],capture_output=True,timeout=15);p.check_returncode();(output/('symbol-%d.s'%i)).write_bytes(p.stdout+p.stderr);assert ('%x:'%address).encode() in p.stdout
  bindings.append({'name':symbol['name'],'unslid_address':hex(address-int(m['slide'],16)),'prefix32_sha256':hashlib.sha256(b).hexdigest(),'direct_probe_segment_container_equal':True,'llvm_disassembled':True})
 result={'image_path':m['path'],'uuid':m['uuid'],'segments':len(segments),'mapped_bytes':m['bytes'],'elf_sha256':hashlib.sha256(payload).hexdigest(),'container_profile':'ARM64 ELF analysis view of own loaded image; live rebased data, ASLR VA, no LINKEDIT; entrypoints resolved only','bindings':bindings,'private_entrypoints_invoked':False,'canvas_protocol_observed':False}
 (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
