from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 images={}
 for name,digest,uuid in [('PreviewsPipeline','c0897c050716f12f88da4dd08c24e3d3ae1de36dc748b65ad0b7346979e40053','c6ed2a5e6f2e3a41a1586d2f65e00a58'),('PreviewsFoundationHost','1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d','6b75229bde5d3d3794bc75af4f4704c6')]:
  p=Path('/Applications/Xcode.app/Contents/SharedFrameworks')/(name+'.framework/Versions/A')/name;m=Image(p);assert hashlib.sha256(m.data).hexdigest()==digest and m.uuid==uuid;images[name]=m
 m=images['PreviewsPipeline'];n=images['PreviewsFoundationHost'];raw=Path(tempfile.mkdtemp(prefix='canvas-execution-ownership-raw-',dir='/private/tmp'));ranges=[]
 for name,a,b,label in [('PreviewsPipeline',0x3e8c10,0x3e8f2c,'update-destroy'),('PreviewsPipeline',0x4894c4,0x489544,'erased-point-destroy'),('PreviewsPipeline',0x489210,0x48924c,'box-deallocate'),('PreviewsFoundationHost',0x41fdc,0x4202c,'handle-deinit-deallocate')]:
  im=images[name];out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(im.path)],capture_output=True,check=True,timeout=20).stdout;(raw/(label+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==im.read(a,b-a)
  ranges.append({'image':name,'name':label,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(im.read(a,b-a)).hexdigest()})
 def fields(im,base):
  kind,size,count=struct.unpack('<HHI',im.read(base+8,8));assert size==12;rows=[]
  for i in range(count):
   a=base+16+i*size;t=a+8+struct.unpack('<i',im.read(a+8,4))[0];buf=bytearray()
   for j in range(200):
    v=im.read(t+j,1)
    if v==b'\0':break
    buf+=v
   else:raise AssertionError('name bound')
   rows.append(buf.decode())
  return rows
 metadata={'update':fields(m,0x55af4c),'erased_point':fields(m,0x55c4cc),'erased_id':fields(m,0x559ffc),'handle':fields(n,0x158638)}
 assert metadata['update']==['output','streamFactory','executionPointID','agentBundle','agentProcess','controlDetails','updatePass','capabilities','symbolicationParameters','publicSuccessfulCompletionDescription','updateSeed','invalidationHandle','usingPipelineV2']
 assert metadata['erased_point']==['box','id'] and metadata['erased_id']==['executionPointType','executionPointID','underlyingDescription','executionPointTypeName'] and metadata['handle']==['name','state']
 types=[]
 for index,name in [(10,'_$s21PreviewsMessagingHost0C10UpdateSeedVMn'),(11,'_$s22PreviewsFoundationHost28ConcurrentInvalidationHandleCMn')]:
  a=0x55af4c+16+12*index+4;t=a+struct.unpack('<i',m.read(a,4))[0];assert m.read(t,1)==b'\x02' and m.read(t+5,1)==b'\0';slot=t+1+struct.unpack('<i',m.read(t+1,4))[0];s=next(s for s in m.sections if s['vm']<=slot<s['vm']+s['length']);actual=m.symbols[m.indirect[s['r1']+(slot-s['vm'])//8]];assert actual==name;types.append({'field':metadata['update'][index],'context':actual})
 for index,typ in [(9,b'SS\0'),(12,b'Sb\0')]:
  a=0x55af4c+16+12*index+4;t=a+struct.unpack('<i',m.read(a,4))[0];assert m.read(t,3)==typ
 expected=[(m,0x3e8ed0,'_$s21PreviewsMessagingHost0C10UpdateSeedVMa'),(m,0x3e8f28,'_swift_release'),(m,0x4894e0,'_swift_release'),(m,0x4894f0,'AnyExecutionPointV2IDVMa'),(m,0x489500,'SendableAnyHashableVMa'),(m,0x489524,'_swift_bridgeObjectRelease'),(m,0x489540,'_swift_bridgeObjectRelease'),(m,0x489248,'_swift_deallocClassInstance'),(n,0x41fe8,'_swift_bridgeObjectRelease'),(n,0x41ff0,'_swift_release'),(n,0x4200c,'_swift_bridgeObjectRelease'),(n,0x42014,'_swift_release'),(n,0x42028,'_swift_deallocClassInstance')]
 calls=[]
 for im,pc,name in expected:
  t=im.resolve(im.branch(pc));ns=[t['name']] if t['kind']=='import_stub' else t['names'];assert any(name in x for x in ns),(hex(pc),t);calls.append({'image':im.path.name,'call':hex(pc),'target':t})
 ops={0x3e8c34:0xf9400821,0x3e8c3c:0xf9400688,0x3e8c40:0xd63f0100,0x3e8edc:0x39414288,0x3e8ee0:0x8b080269,0x3e8ee4:0x91004129,0x3e8ee8:0x8a280133,0x3e8eec:0xf9400688,0x3e8ef4:0xd63f0100,0x3e8ef8:0xf9402288,0x3e8efc:0x8b130108,0x3e8f00:0x91001d08,0x3e8f04:0x927df108,0x3e8f08:0xf9400100,0x4894dc:0xf9400000,0x4894e4:0xb9801668,0x4894f8:0xb9801415,0x48950c:0xf9400508,0x489514:0xd63f0100,0x489518:0xb9801a68,0x489528:0xb9801e68,0x489220:0xf9405101,0x489228:0xf9400508,0x489230:0xd63f0100}
 for pc,v in ops.items():assert m.word(pc)==v,hex(pc)
 # This absence claim is restricted to the complete tiny handle deinit bodies.
 branches=[]
 for pc in range(0x41fdc,0x4202c,4):
  v=n.word(pc)
  if v>>26 in (5,37):branches.append(pc)
  assert v&0xfffffc1f not in (0xd63f0000,0xd61f0000)
 assert branches==[0x41fe8,0x41ff0,0x4200c,0x42014,0x42028]
 result={'images':{k:{'sha256':hashlib.sha256(im.data).hexdigest(),'uuid':im.uuid,'architecture':'arm64'} for k,im in images.items()},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'metadata':metadata,'update_field_type_bindings':types,'calls':calls,'source_policy':{'update':'Generic output is destroyed through its type witness. At tail, after publicSuccessfulCompletionDescription String cleanup, typed UpdateSeed is destroyed; its size/alignment advances to the reflected ConcurrentInvalidationHandle field and swift_release is tail-called. Other update fields are byte-verified but not fully semantically mapped here.','erased_point':'Destroy releases box reference, destroys SendableAnyHashable executionPointID, then releases the two ID string backing values. executionPointType metadata is not separately released by this route.','box_deallocate':'If concrete generic box deallocation runs, destroy stored generic value through its witness then deallocate class instance. This is not proof release of the outer value reaches this deallocation.','handle_deinit':'Deinit directly bridge-releases name backing value and releases state reference; deallocating variant additionally deallocates class storage. Complete bounded bodies have no explicit invalidate/observer call. Released state object and dynamic payload effects remain opaque.','boundaries':'A release/deinit/deallocation source path does not establish zero reference count, actual callback cancellation, session invalidation or OS/transport settlement. Full ExecutionPointStatus and dynamic state/viewable witnesses remain unqualified.'},'scope':{'static_only':True,'native_private_calls':0,'actual_lifetime_or_cancellation_control':False,'full_canvas_parity':False},'limitations':['ExecutionPointStatus destructor explored locally but not semantically qualified in this update/erased-point unit.','Prior locked-screen/Accessibility and Ghidra failures not retried unchanged.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls':len(calls),'native_controls':0}))
