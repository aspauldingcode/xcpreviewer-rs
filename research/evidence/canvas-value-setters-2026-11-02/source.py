from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsUI.framework/Versions/A/PreviewsUI');m=Image(p)
 assert hashlib.sha256(m.data).hexdigest()=='26037ce436a19205977e4c5b879c8b46a1ac87f19fef25ffb5e14282ba189fab' and m.uuid=='0d87b0e2f4453035a9b6b1cf8230e015'
 raw=Path(tempfile.mkdtemp(prefix='canvas-value-setters-raw-',dir='/private/tmp'));ranges=[]
 for a,b,label in [(0x16be4,0x16bf0,'item-setter'),(0x16cf0,0x16d20,'content-setter'),(0x8b490,0x8b4c0,'registry-preview-setter'),(0x16d20,0x16d70,'optional-content-assign'),(0x480f0,0x48140,'optional-preview-assign'),(0x19dd4,0x19e0c,'shared-assign'),(0x1b610,0x1b6b0,'preview-destroy-prefix')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(raw/(label+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'name':label,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 expected={0x16d04:'PreviewVMa',0x8b4a4:'RegistryVMa',0x16d44:'___swift_instantiateConcreteTypeFromMangledNameV2',0x48114:'___swift_instantiateConcreteTypeFromMangledNameV2',0x1b63c:'_$s16PreviewsPipeline14DiscoveredItemOMa',0x1b65c:'_swift_release',0x1b66c:'PreviewV06CanvasD0OMa'}
 calls=[]
 for a,name in expected.items():
  t=m.resolve(m.branch(a));names=[t['name']] if t['kind']=='import_stub' else t['names'];assert any(name in n for n in names),(hex(a),t);calls.append({'call':hex(a),'target':t})
 for a,target,name in [(0x16bec,0x19dd4,'DiscoveredItemOvsTm'),(0x16d1c,0x16d20,'CanvasD0OSgWOd'),(0x8b4bc,0x480f0,'PreviewVSgWOd')]:assert m.branch(a)==target and any(name in n for n in m.named[target])
 def fields(base):
  kind,size,count=struct.unpack('<HHI',m.read(base+8,8));assert kind==0 and size==12;names=[]
  for i in range(count):
   a=base+16+i*size;t=a+8+struct.unpack('<i',m.read(a+8,4))[0];buf=bytearray()
   for j in range(200):
    v=m.read(t+j,1)
    if v==b'\0':break
    buf+=v
   else:raise AssertionError('field string length')
   names.append(buf.decode())
  return names
 preview=fields(0xb73d8);registry=fields(0xb84a0)
 assert preview==['item','settingsRelay','canvasContent'] and registry==['definition','isPinned','status','preview']
 a=0xc1a88;sec=next(s for s in m.sections if s['vm']<=a<s['vm']+s['length']);assert sec['flags']&255==6;typ=m.symbols[m.indirect[sec['r1']+(a-sec['vm'])//8]];assert typ=='_$s16PreviewsPipeline14DiscoveredItemOMa'
 ops={0x16d08:0xb9801808,0x16d0c:0x8b080281,0x8b4a8:0xb9801c08,0x8b4ac:0x8b080281,0x16d50:0xf9401508,0x16d54:0xaa1303e0,0x16d58:0xaa1403e1,0x16d5c:0xd63f0100,0x48120:0xf9401508,0x48124:0xaa1303e0,0x48128:0xaa1403e1,0x4812c:0xd63f0100,0x19df4:0xf9401503,0x19e08:0xd61f0060,0x1b648:0xf9400508,0x1b650:0xd63f0100,0x1b654:0xb9801668,0x1b658:0xf8686a80,0x1b660:0xb9801a68,0x1b678:0xf9401908,0x1b680:0x52800021,0x1b688:0xd63f0100,0x1b68c:0x34000120,0x1b6ac:0xd65f03c0}
 for a,v in ops.items():assert m.word(a)==v,hex(a)
 result={'image':{'sha256':hashlib.sha256(m.data).hexdigest(),'uuid':m.uuid,'architecture':'arm64'},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'calls':calls,'item_type_import':typ,'field_metadata':{'Preview':preview,'Registry':registry},'source_policy':{'item_setter':'Loads DiscoveredItem metadata function and delegates to shared assignment helper; helper invokes metadata then tail-calls value witness at offset 0x28.','content_setter':'Uses Preview metadata field offset at 0x18 for canvasContent destination, then optional CanvasContent assignment helper, which invokes typed witness at offset 0x28.','registry_preview_setter':'Uses Registry metadata field offset at 0x1c for preview destination, then optional Preview assignment helper, which invokes typed witness at offset 0x28.','callbacks':'No explicit lifecycle/event callback in these bounded setter/assignment fragments. Dynamic value-witness effects are not covered by that statement.','preview_destroy_prefix':'Destroy item through its typed witness; load settingsRelay at metadata field offset 0x14 and call swift_release; then inspect canvasContent at field offset 0x18. Valid absent optional returns, present continues at 0x1b6b0 beyond this semantic scope.','boundaries':'A release call does not prove reference count reaches zero, relay deinit, downstream session invalidation or final OS/transport settlement. Full optional assignment witness implementations and present canvas payload destruction remain unqualified.'},'scope':{'static_only':True,'native_private_calls':0,'runtime_release_or_settlement_observed':False,'full_payload_destruction_or_canvas_parity':False},'failures':['First Registry field-name read requested 80 bytes across a section boundary and failed safely. Corrected bounded bytewise NUL string reader verifies names.','Destruction witnesses inspected and large assignment witnesses inventoried locally; only explicit prefix destruction semantics are qualified here.','Prior locked-screen/Accessibility and Ghidra failures not retried unchanged.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls':len(calls),'setter_tail_bindings':3}))
