from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsUI.framework/Versions/A/PreviewsUI');m=Image(p)
 assert hashlib.sha256(m.data).hexdigest()=='26037ce436a19205977e4c5b879c8b46a1ac87f19fef25ffb5e14282ba189fab' and m.uuid=='0d87b0e2f4453035a9b6b1cf8230e015'
 a,b=0x23ef0,0x24680;raw=Path(tempfile.mkdtemp(prefix='canvas-state-destroy-raw-',dir='/private/tmp'))
 out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(raw/'continuation.raw.s').write_bytes(out)
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
 assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
 def fields(base):
  kind,size,count=struct.unpack('<HHI',m.read(base+8,8));assert size==12;rows=[]
  for i in range(count):
   x=base+16+i*size;t=x+8+struct.unpack('<i',m.read(x+8,4))[0];buf=bytearray()
   for j in range(200):
    v=m.read(t+j,1)
    if v==b'\0':break
    buf+=v
   else:raise AssertionError('field name length')
   rows.append(buf.decode())
  return rows
 metadata={k:fields(x) for k,x in [('state',0xb795c),('pending',0xb79a8),('updating',0xb79d0),('viewable',0xb7a04),('viewable_status',0xb7a38),('failed_reason',0xb7a60),('canvas_preview',0xb7490),('variant_matrix',0xb7544)]}
 for k,names in {'state':['disabled','enabledExpectingUpdate','updating','succeeded','failed'],'pending':['capabilities','configuration'],'updating':['groupSeed','capabilities','configuration'],'viewable':['status','capabilities','configuration'],'viewable_status':['valid','stale'],'failed_reason':['failed','canceled'],'variant_matrix':['groups']}.items():assert metadata[k]==names
 for base,payload,empty in [(0xb1dec,5,0),(0xb1e8c,2,0),(0xb1eb4,1,1)]:
  word,nempty=struct.unpack('<II',m.read(base+20,8));assert word&0xffffff==payload and nempty==empty
 groups_symbol='_$s10PreviewsUI18DisplayableContentV7PreviewV06CanvasE0V13VariantMatrixV6groupsSayAG0G5GroupVGvg'
 assert groups_symbol in m.named[0x1988]
 # Native chained-fixup format is required for indirect symbolic references to
 # local nominal descriptors; imported GOT entries use indirect symbol indices.
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
  assert value>>63==0 and (value>>36)&255==0;dest=value&((1<<36)-1);ns=m.named.get(dest,[]);assert len(ns)==1 and ns[0].endswith('Mn');return ns[0]
 type_refs=[]
 for ref,expected,literal in [(0xad810,['PendingF0VMn','ViewableVMn'],'5state_Sg8previoust'),(0xad820,['UpdatingF0VMn','ViewableVMn'],'5state_Sg8previoust'),(0xad830,['FailedReasonOMn','UpdatingF0VMn','ViewableVMn'],'6reason_6updateSg8previoust'),(0xaeb50,['ExecutionPointUpdateVMn','PreviewViewableMp'],'y_pG')]:
  rel,length=struct.unpack('<iI',m.read(ref,8));base=ref+rel;blob=m.read(base,length);assert length<128;names=[];text='';i=0
  while i<len(blob):
   v=blob[i]
   if v==2:
    addr=base+i+1;names.append(context(addr+struct.unpack('<i',m.read(addr,4))[0]));i+=5
   else:assert v>=32;text+=chr(v);i+=1
  assert len(names)==len(expected) and all(x in y for x,y in zip(expected,names)) and text==literal,(hex(ref),names,text)
  type_refs.append({'reference':hex(ref),'contexts':names,'literal_mangling':text})
 def signed(x,bits):return x-(1<<bits) if x&(1<<(bits-1)) else x
 def route(pc,tag,ends):
  diff=None;visited=[]
  for _ in range(16):
   if pc in ends:return pc,visited
   visited.append(hex(pc));v=m.word(pc)
   if v&0xffc003ff==0x7100001f:diff=tag-((v>>10)&4095);pc+=4
   elif v&0xff000010==0x54000000:
    cond=v&15;assert cond in [0,1,13];take={0:diff==0,1:diff!=0,13:diff<=0}[cond];pc=pc+4*signed((v>>5)&0x7ffff,19) if take else pc+4
   elif v&0xff00001f==0x34000000:pc=pc+4*signed((v>>5)&0x7ffff,19) if tag==0 else pc+4
   else:raise AssertionError((hex(pc),hex(v)))
  raise AssertionError('dispatch bound')
 dispatch=[]
 for label,pc,entries in [('live',0x23f08,[0x24038,0x24038,0x240b4,0x24190,0x23f28]),('static',0x242c8,[0x243e8,0x243e8,0x24464,0x24540,0x242e8])]:
  for tag,name in enumerate(metadata['state']):
   entry,visited=route(pc,tag,set(entries));assert entry==entries[tag];dispatch.append({'field':label,'state':name,'entry':hex(entry),'visited':visited})
 expected={0x23ef4:'PreviewV5StateOMa',0x23f04:'_swift_getEnumCaseMultiPayload',0x23f30:'_swift_errorRelease',0x24060:'PendingF0VMa',0x240b8:'UpdatingF0VMa',0x24144:'ViewableVMa',0x24178:'_swift_getEnumCaseMultiPayload',0x24188:'destroy_boxed_opaque_existential',0x241b0:'destroy_boxed_opaque_existential',0x242c4:'_swift_getEnumCaseMultiPayload',0x242f0:'_swift_errorRelease',0x24410:'PendingF0VMa',0x24468:'UpdatingF0VMa',0x24544:'ViewableV6StatusOMa',0x24550:'_swift_getEnumCaseMultiPayload',0x24560:'destroy_boxed_opaque_existential',0x245d0:'ViewableVMa',0x245f0:'PreviewConfigurationVMa',0x2467c:'_swift_bridgeObjectRelease'}
 calls=[]
 for pc,name in expected.items():
  t=m.resolve(m.branch(pc));ns=[t['name']] if t['kind']=='import_stub' else t['names'];assert any(name in n for n in ns),(hex(pc),t);calls.append({'call':hex(pc),'target':t})
 ops={0x2404c:0x35000080,0x2408c:0x350000a0,0x240d8:0x35000080,0x24110:0x350000a0,0x24164:0x35000a80,0x24180:0x540001c1,0x241a8:0x540002a1,0x242b4:0xb9802688,0x243fc:0x35000080,0x24558:0x54000261,0x24658:0xb9802a88,0x2465c:0xf8686a60}
 for pc,v in ops.items():assert m.word(pc)==v,hex(pc)
 result={'image':{'sha256':hashlib.sha256(m.data).hexdigest(),'uuid':m.uuid,'architecture':'arm64'},'range':{'start':'0x23ef0','end_exclusive':'0x24680','bytes':1936,'sha256':hashlib.sha256(m.read(0x23ef0,1936)).hexdigest()},'source_bytes_verified':1936,'metadata':metadata,'type_references':type_refs,'variant_groups_type_symbol':groups_symbol,'dispatch':dispatch,'calls':calls,'source_policy':{'state_routes':'Both livePreview and staticPreview state dispatch map disabled/enabledExpectingUpdate to pending cleanup, updating to updating cleanup, succeeded to Viewable cleanup, failed to reason/update/previous cleanup.','pending_updating':'Destroy capabilities/configuration only when their optional payloads are present, then clean previous Viewable only when present. Pending/Updating concrete tuple references and fields are independently bound.','failed':'Pass failure-reason reference representation to swift_errorRelease, clean updating fields and optional previous Viewable. FailedReason also has canceled empty case; no actual error presence or runtime cancellation inferred.','viewable':'valid status delegates to ExecutionPointUpdate<PreviewViewable existential> witness; stale status destroys its opaque existential container. Viewable capabilities/configuration cleanup follows. Contained values and callback/resource effects remain opaque.','variant_matrix':'After both state cleanups, load variantMatrix groups reference and tail-call swift_bridgeObjectRelease. No per-element destruction or final deallocation observed by this source-only unit.'},'scope':{'static_only':True,'native_private_calls':0,'actual_lifetime_or_cancellation_control':False,'dynamic_witness_contents_or_full_canvas_parity':False},'failures':['Initial exploratory symbolic-reference reader assumed every GOT slot was imported and hit an indirect-local sentinel. Corrected resolver validates chained-fixup format 6 and walks the relevant page chain before resolving local nominal descriptors.','One exploratory follow-up command had unmatched bracket syntax and failed before executing; no inference from failure.','First verifier reused the load-command size variable for chained-segment structure size and failed a bounds read. Separate command-size variable fixes the reader; failed source retained locally.','Prior UI/Ghidra failures not retried unchanged.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':1936,'selected_calls':len(calls),'state_dispatch_cases':len(dispatch)}))
