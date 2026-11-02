from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsPipeline.framework/Versions/A/PreviewsPipeline');m=Image(p)
 assert hashlib.sha256(m.data).hexdigest()=='c0897c050716f12f88da4dd08c24e3d3ae1de36dc748b65ad0b7346979e40053' and m.uuid=='c6ed2a5e6f2e3a41a1586d2f65e00a58'
 a,b=0x293cb4,0x294254;raw=Path(tempfile.mkdtemp(prefix='canvas-execution-status-raw-',dir='/private/tmp'))
 out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(raw/'status.raw.s').write_bytes(out)
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
 assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
 assert '_$s16PreviewsPipeline20ExecutionPointStatusOwxx' in m.named[a]
 base=0x5590c4;kind,size,count=struct.unpack('<HHI',m.read(base+8,8));assert (kind,size,count)==(2,12,3)
 fields=[];refs=[]
 for i in range(count):
  rec=base+16+12*i;n=rec+8+struct.unpack('<i',m.read(rec+8,4))[0];buf=bytearray()
  for j in range(200):
   v=m.read(n+j,1)
   if v==b'\0':break
   buf+=v
  else:raise AssertionError('name bound')
  fields.append(buf.decode());refs.append(rec+4+struct.unpack('<i',m.read(rec+4,4))[0])
 assert fields==['running','valid','failed'] and refs==[0x54ba18,0x54ba34,0x54ba54]
 word,empty=struct.unpack('<II',m.read(0x5652bc+20,8));assert word&0xffffff==3 and empty==0
 segments=[];at=32
 for _ in range(struct.unpack_from('<I',m.data,16)[0]):
  cmd,cmdsize=struct.unpack_from('<II',m.data,at)
  if cmd==0x80000034:
   off,sz=struct.unpack_from('<II',m.data,at+8);header=struct.unpack_from('<7I',m.data,off);assert header[0]==0;start=off+header[1];count=struct.unpack_from('<I',m.data,start)[0]
   for i in range(count):
    rel=struct.unpack_from('<I',m.data,start+4+i*4)[0]
    if rel:
     pos=start+rel;size,page,fmt,vm,maxptr,npages=struct.unpack_from('<IHHQIH',m.data,pos);assert fmt==6 and size>=22+2*npages;segments.append((vm,page,npages,pos+22))
  at+=cmdsize
 def context(slot):
  sec=next(s for s in m.sections if s['vm']<=slot<s['vm']+s['length']);assert sec['flags']&255==6;ix=m.indirect[sec['r1']+(slot-sec['vm'])//8]
  if ix<len(m.symbols):return m.symbols[ix]
  assert ix==0x80000000
  vm,page,npages,starts=next(x for x in segments if x[0]<=slot<x[0]+x[1]*x[2]);page_index=(slot-vm)//page;first=struct.unpack_from('<H',m.data,starts+2*page_index)[0];assert first<0x8000;pc=vm+page_index*page+first
  for _ in range(4096):
   value=struct.unpack('<Q',m.read(pc,8))[0]
   if pc==slot:break
   step=(value>>51)&4095;assert step and pc<slot;pc+=4*step
  else:raise AssertionError('fixup walk bound')
  assert value>>63==0 and (value>>36)&255==0;dest=value&((1<<36)-1);ns=m.named.get(dest,[]);assert len(ns)==1 and ns[0].endswith(('Mn','Mp'));return ns[0]
 type_refs=[]
 for ref in refs:
  i=0;text='';names=[]
  while i<128:
   v=m.read(ref+i,1)[0]
   if v==0:break
   if v==2:
    addr=ref+i+1;names.append(context(addr+struct.unpack('<i',m.read(addr,4))[0]));i+=5
   else:assert v>=32;text+=chr(v);i+=1
  else:raise AssertionError('type reference bound')
  type_refs.append({'reference':hex(ref),'contexts':names,'literal_mangling':text})
 assert [x['literal_mangling'] for x in type_refs]==['6OutputQzSg05staleA0_t','y6OutputQzG6update_t','6OutputQzSg05staleA0__p5errort']
 ep='_$s16PreviewsPipeline14ExecutionPointMp';up='_$s16PreviewsPipeline20ExecutionPointUpdateVMn'
 assert [x['contexts'] for x in type_refs]==[[ep],[up,ep],[ep,'_$ss5ErrorMp']]
 assert '_$s6Output16PreviewsPipeline14ExecutionPointPTl' in m.named[0x5644d0]
 expected={0x293cf4:'_swift_getAssociatedTypeWitness',0x293d20:'SendableAnyHashableVMa',0x293d68:'Foundation3URLVMa',0x293e0c:'CrashLogSymbolicationParametersVMa',0x293e48:'UpdateSeedVMa',0x294168:'_swift_release',0x294250:'_swift_errorRelease'}
 calls=[]
 for pc,name in expected.items():
  target=m.resolve(m.branch(pc));ns=[target['name']] if target['kind']=='import_stub' else target['names'];assert any(name in n for n in ns);calls.append({'call':hex(pc),'target':target})
 # Logical payload tag dispatch after the generic enum representation decoder.
 assert m.word(0x293efc)==0x7100095f and m.word(0x293f04)==0x7100055f
 def conditional(pc,condition):
  v=m.word(pc);assert v&0xff000010==0x54000000 and v&15==condition
  offset=(v>>5)&0x7ffff;offset=offset-(1<<19) if offset&(1<<18) else offset
  return pc+4*offset
 assert conditional(0x293f00,0)==0x2941f8 and conditional(0x293f08,1)==0x29416c
 dispatch=[{'tag':0,'case':'running','entry':'0x29416c'},{'tag':1,'case':'valid','entry':'0x293f0c'},{'tag':2,'case':'failed','entry':'0x2941f8'}]
 ops={0x293cd8:0xa9412022,0x293cdc:0xb0001683,0x293ce0:0x9112c063,0x293ce4:0xb0001684,0x293ce8:0x91134084,0x293f30:0xf9400508,0x293f38:0xd63f0100,0x294170:0xf9401a88,0x294178:0x52800021,0x294180:0xd63f0100,0x294184:0x34000120,0x2941a8:0xf9400682,0x2941d0:0xd61f0040,0x2941fc:0xf9401a88,0x294204:0x52800021,0x29420c:0xd63f0100,0x294210:0x350000a0,0x294214:0xf9400688,0x294220:0xd63f0100,0x294224:0x8b1802a8,0x294228:0x91001d08,0x29422c:0x927df108,0x294230:0xf9400100,0x29412c:0xa94307e8,0x294130:0xf9400508,0x294138:0xd63f0100,0x29413c:0xf94017e8,0x294140:0x8b130108,0x294144:0x927df108,0x294148:0xf9400100}
 for pc,v in ops.items():assert m.word(pc)==v,hex(pc)
 result={'image':{'sha256':hashlib.sha256(m.data).hexdigest(),'uuid':m.uuid,'architecture':'arm64'},'range':{'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()},'source_bytes_verified':b-a,'fields':fields,'payload_case_count':3,'empty_case_count':0,'type_references':type_refs,'dispatch':dispatch,'calls':calls,'source_policy':{'running':'Payload is optional associated ExecutionPoint.Output named staleOutput. Probe its optional enum tag via associated output value witness; absent returns, present tail-delegates output destruction.','valid':'Payload is ExecutionPointUpdate<ExecutionPoint.Output> named update. This witness inlines cleanup: associated output destroy, intermediate cleanup, final reference release. Intermediate field-to-operation mapping is not complete here; no extra call to the standalone update destroy function is inferred.','failed':'Payload has optional associated Output staleOutput plus Error. Destroy staleOutput only when present, then load aligned following error reference and tail-call swift_errorRelease.','boundary':'Associated output metadata comes from ExecutionPoint protocol and Output requirement descriptors. Generic enum representation decoder bytes are checked, but arbitrary malformed representations and runtime layout sizes are not exercised. Reference releases and dynamic witnesses do not prove cancellation or final resource settlement.'},'scope':{'static_only':True,'native_private_calls':0,'actual_lifetime_or_cancellation_control':False,'full_canvas_parity':False},'failures':['Exploratory types.py shadowed Python standard-library types and failed import; renamed field_types.py before analysis.','Prior UI/Ghidra failures not retried unchanged.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':b-a,'selected_calls':len(calls),'logical_dispatch_routes':len(dispatch)}))
