from pathlib import Path
import fcntl,hashlib,json,re,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 images={}
 for name,digest,uuid in [('PreviewsScenes','e785b5947cd0ae70ff8977485f73f7181b6ed07c958ef29ce263ffa06397bc09','afaf513ac1153755840e1d82b40e7d93'),('PreviewsUI','26037ce436a19205977e4c5b879c8b46a1ac87f19fef25ffb5e14282ba189fab','0d87b0e2f4453035a9b6b1cf8230e015')]:
  p=Path('/Applications/Xcode.app/Contents/SharedFrameworks')/(name+'.framework/Versions/A')/name;m=Image(p);assert hashlib.sha256(m.data).hexdigest()==digest and m.uuid==uuid;images[name]=m
 m=images['PreviewsScenes'];n=images['PreviewsUI'];raw=Path(tempfile.mkdtemp(prefix='canvas-preview-update-raw-',dir='/private/tmp'));ranges=[]
 for name,a,b,label in [('PreviewsScenes',0x3f694,0x3fa5c,'update'),('PreviewsUI',0x187a8,0x187b4,'instance-setter'),('PreviewsUI',0x19dd4,0x19e0c,'value-assign')]:
  im=images[name];out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(im.path)],capture_output=True,check=True,timeout=20).stdout;(raw/(label+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==im.read(a,b-a)
  ranges.append({'image':name,'name':label,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(im.read(a,b-a)).hexdigest()})
 expected={0x3f6c0:'PreviewV06CanvasE0VMa',0x3f780:'PreviewInstanceVMa',0x3f7d8:'DiscoveredItemOMa',0x3f848:'PreviewV4item0A8Pipeline14DiscoveredItemOvs',0x3f8b0:'PreviewV06canvasD0AE06CanvasD0OSgvg',0x3f8b8:'PreviewV06CanvasD0OMa',0x3f974:'PreviewV06CanvasE0V8instance0A8Pipeline0E8InstanceVvs',0x3f9c4:'PreviewV06canvasD0AE06CanvasD0OSgvs',0x3fa54:'_diagnoseUnexpectedEnumCase'}
 calls=[]
 for a,name in expected.items():
  t=m.resolve(m.branch(a));assert name in t['name'],(hex(a),t);calls.append({'call':hex(a),'target':t})
 imports={}
 for im,a,name in [(m,0x95c98,'_$s16PreviewsPipeline14DiscoveredItemO7previewyAcA15PreviewInstanceVcACmFWC'),(m,0x967d8,'_$s10PreviewsUI18DisplayableContentV7PreviewV06CanvasD0O7previewyAgE0fE0VcAGmFWC'),(m,0x967e0,'_$s10PreviewsUI18DisplayableContentV7PreviewV06CanvasD0O8registryyAgE0F8RegistryVcAGmFWC'),(n,0xc1b88,'_$s16PreviewsPipeline15PreviewInstanceVMa')]:
  sec=next(s for s in im.sections if s['vm']<=a<s['vm']+s['length']);assert sec['flags']&255==6;actual=im.symbols[im.indirect[sec['r1']+(a-sec['vm'])//8]];assert actual==name;imports[im.path.name+':'+hex(a)]=actual
 ops={0x3f87c:0x54000b61,0x3f8d8:0x7100041f,0x3f8e0:0x540009e0,0x3f904:0x540007a1,0x3f93c:0xf9400ab8,0x3f950:0xd63f0300,0x3f968:0xd63f0100,0x3f978:0xf85783b4,0x3f98c:0xf85a83b8,0x3f99c:0xaa1303e2,0x3f9ac:0x52800001,0x3f9b0:0x52800022,0x3fa08:0x54000221,0x3fa58:0xd4200020}
 for a,v in ops.items():assert m.word(a)==v,hex(a)
 assert n.branch(0x187b0)==0x19dd4 and any('item0A8Pipeline14DiscoveredItemOvsTm' in x for x in n.named[0x19dd4])
 for a,v in {0x187ac:0xf945c421,0x19de8:0xd63f0020,0x19df4:0xf9401503,0x19df8:0xaa1403e0,0x19dfc:0xaa1303e1,0x19e08:0xd61f0060}.items():assert n.word(a)==v,hex(a)
 result={'images':{k:{'sha256':hashlib.sha256(v.data).hexdigest(),'uuid':v.uuid,'architecture':'arm64'} for k,v in images.items()},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'calls':calls,'imports':imports,'source_policy':{'item_assignment':'Always assign incoming DiscoveredItem to Preview.item before testing its case.','non_preview_item':'Incoming item other than preview skips canvas-content synchronization after item assignment.','canvas_guard':'For preview item, read optional canvasContent; absent skips creation/update. Present registry content skips instance synchronization. Unexpected content enum case diagnoses/traps.','preview_content':'Copy existing CanvasPreview, assign new PreviewInstance, wrap the same preview content case as present optional and write canvasContent back. Other CanvasPreview fields are carried by the value copy; this does not establish full application/state preservation.','instance_setter':'Independently pinned PreviewsUI setter loads PreviewInstance metadata function and tails to shared helper. Helper obtains that metadata and tail-calls its value witness at offset 0x28 using destination self and incoming value. No explicit extra callback in these setter/helper fragments.','boundaries':'Item/canvasContent setter internals, value-witness resource release, notifications, completed render, session/state continuity and registry reconciliation remain unqualified.'},'scope':{'static_only':True,'private_native_calls':0,'native_runtime_control':False,'full_state_preservation_or_resource_settlement_observed':False,'full_canvas_parity':False},'limitations':['Prior locked-screen/empty Accessibility and unresponsive Ghidra failures not retried unchanged.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls':len(calls),'case_and_type_imports':len(imports)}))
