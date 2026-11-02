from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 ui=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsUI.framework/Versions/A/PreviewsUI');pl=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsPipeline.framework/Versions/A/PreviewsPipeline');m=Image(ui);n=Image(pl)
 assert hashlib.sha256(m.data).hexdigest()=='26037ce436a19205977e4c5b879c8b46a1ac87f19fef25ffb5e14282ba189fab' and m.uuid=='0d87b0e2f4453035a9b6b1cf8230e015'
 assert hashlib.sha256(n.data).hexdigest()=='c0897c050716f12f88da4dd08c24e3d3ae1de36dc748b65ad0b7346979e40053' and n.uuid=='c6ed2a5e6f2e3a41a1586d2f65e00a58'
 a,b=0x23d68,0x23ef0;raw=Path(tempfile.mkdtemp(prefix='canvas-content-destroy-raw-',dir='/private/tmp'))
 out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(ui)],capture_output=True,check=True,timeout=20).stdout;(raw/'destroy-prefix.raw.s').write_bytes(out)
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
 assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
 expected={0x23d8c:'_swift_getEnumCaseMultiPayload',0x23d9c:'RegistryCapabilitiesVMa',0x23db8:'CanvasRegistryVMa',0x23dc8:'IdentifierVMa',0x23de4:'CanvasRegistryV6StatusVMa',0x23dfc:'___swift_instantiateConcreteTypeFromMangledNameV2',0x23e34:'PreviewInstanceVMa',0x23e50:'PreviewV06CanvasE0VMa',0x23e60:'PreviewConfigurationV8LocationVMa',0x23e80:'PreviewCapabilitiesVMa',0x23ea4:'EditorSettingsV10CanvasModeOMa',0x23eb0:'_swift_getEnumCaseMultiPayload',0x23ec4:'ExecutionPointPropertiesV12HostLocationOMa',0x23ed0:'PreviewVariantGroupVMa'}
 calls=[]
 for a,name in expected.items():
  t=m.resolve(m.branch(a));ns=[t['name']] if t['kind']=='import_stub' else t['names'];assert any(name in x for x in ns),(hex(a),t);calls.append({'call':hex(a),'target':t})
 def fields(im,base):
  kind,size,count=struct.unpack('<HHI',im.read(base+8,8));assert size==12;rows=[]
  for i in range(count):
   a=base+16+i*size;t=a+8+struct.unpack('<i',im.read(a+8,4))[0];buf=bytearray()
   for j in range(200):
    v=im.read(t+j,1)
    if v==b'\0':break
    buf+=v
   else:raise AssertionError('field string')
   rows.append({'name':buf.decode(),'payload_type_present':bool(im.word(a+4))})
  return rows
 data={name:fields(im,base) for name,im,base in [('content',m,0xb740c),('registry',m,0xb7434),('status',m,0xb7468),('preview',m,0xb7490),('canvas_mode',n,0x557058)]}
 for key,names in {'content':['preview','registry'],'registry':['capabilities','enabled','status'],'status':['id','executionStatus'],'preview':['instance','location','capabilities','canvasMode','livePreview','staticPreview','variantMatrix'],'canvas_mode':['live','grid','static']}.items():assert [x['name'] for x in data[key]]==names
 assert [x['payload_type_present'] for x in data['canvas_mode']]==[True,True,False]
 payload_word,empty_count=struct.unpack('<II',n.read(0x5630e8+20,8));assert payload_word&0xffffff==2 and empty_count==1
 # Resolve concrete executionStatus type from V2 relative type reference and
 # its two indirect symbolic context references into native GOT imports.
 rel,length=struct.unpack('<iI',m.read(0xaf100,8));base=0xaf100+rel;blob=m.read(base,length);assert length==12 and blob[0]==blob[6]==2 and blob[5:6]==b'y' and blob[11:]==b'G'
 symbols=[]
 for delta in [0,6]:
  ref=base+delta+1;dest=ref+struct.unpack('<i',m.read(ref,4))[0];sec=next(s for s in m.sections if s['vm']<=dest<s['vm']+s['length']);assert sec['flags']&255==6;symbols.append(m.symbols[m.indirect[sec['r1']+(dest-sec['vm'])//8]])
 assert symbols==['_$s16PreviewsPipeline20ExecutionPointStatusOMn','_$s16PreviewsPipeline17AnyExecutionPointVMn']
 ops={0x23d90:0x7100041f,0x23d94:0x540004e1,0x23da8:0xf9400508,0x23db0:0xd63f0100,0x23dbc:0xb9801808,0x23dd4:0xf9400508,0x23ddc:0xd63f0100,0x23de8:0xb9801414,0x23df4:0x90000461,0x23df8:0x91040021,0x23e08:0xf9400502,0x23e2c:0xd61f0040,0x23e40:0xf9400508,0x23e48:0xd63f0100,0x23e58:0xb9801415,0x23e74:0xd63f0100,0x23e78:0xb9801a96,0x23e98:0xd63f0340,0x23e9c:0xb9801e96,0x23eb4:0x7100041f,0x23eb8:0x540000a0,0x23ebc:0x35000160,0x23ec8:0x14000003,0x23ee4:0xd63f0100,0x23ee8:0xb9802288}
 for a,v in ops.items():assert m.word(a)==v,hex(a)
 result={'images':{x.path.name:{'sha256':hashlib.sha256(x.data).hexdigest(),'uuid':x.uuid,'architecture':'arm64'} for x in [m,n]},'range':{'start':'0x23d68','end_exclusive':'0x23ef0','bytes':392,'sha256':hashlib.sha256(m.read(0x23d68,392)).hexdigest()},'source_bytes_verified':392,'calls':calls,'fields':data,'execution_status_type_imports':symbols,'destruction_edges':[{'field':f,'delegated_type':t,'call':a,'relation':'typed destroy witness','evidence':'static source only'} for f,t,a in [('registry.capabilities','RegistryCapabilities','0x23db0'),('registry.status.id','Identifier','0x23ddc'),('registry.status.executionStatus','ExecutionPointStatus<AnyExecutionPoint>','0x23e2c'),('preview.instance','PreviewInstance','0x23e48'),('preview.location','PreviewConfiguration.Location','0x23e74'),('preview.capabilities','PreviewCapabilities','0x23e98'),('preview.canvasMode.live','HostLocation','0x23ee4'),('preview.canvasMode.grid','PreviewVariantGroup','0x23ee4')]],'source_policy':{'registry':'Registry enum payload destroys capabilities through RegistryCapabilities witness, then status.id through Identifier witness, then status.executionStatus through ExecutionPointStatus<AnyExecutionPoint> witness. enabled is a scalar field; no separate owned-field cleanup established for it.','preview_prefix':'Preview payload destroys instance through PreviewInstance witness, location through PreviewConfiguration.Location witness, then capabilities through PreviewCapabilities witness.','canvas_mode':'Native mode reflection binds live payload to HostLocation cleanup and grid payload to PreviewVariantGroup cleanup. static has no payload cleanup on this route.','next_boundary':'After mode cleanup, compute livePreview state field address. State, staticPreview and variantMatrix destruction remain outside this semantic unit.','scope':'Typed value-destruction delegation only. These dynamic witnesses are not traced here; no execution-point cancellation, task invalidation, callback completion, renderer release or final resource settlement inferred.'},'scope':{'static_only':True,'native_private_calls':0,'actual_lifetime_control':False,'full_payload_destruction_or_canvas_parity':False},'failures':['An exploratory type-reference command contained an invalid placeholder and failed before execution. Corrected read resolves the two indirect native type imports; no type inference from failed command.','Initial CanvasMode count assertion compared the packed payload-count/offset word directly. Corrected low-24-bit count extraction passes; failed reader retained locally.','Prior locked-screen/Accessibility and Ghidra failures not retried unchanged.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':392,'selected_calls':len(calls),'mode_cases':[x['name'] for x in data['canvas_mode']]}))
