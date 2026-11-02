from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
root=Path('/Users/8amps/xcpreviewer-rs');here=Path(__file__).parent
with (root/'research/state/controller.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsScenes.framework/Versions/A/PreviewsScenes');m=Image(p)
 assert hashlib.sha256(m.data).hexdigest()=='e785b5947cd0ae70ff8977485f73f7181b6ed07c958ef29ce263ffa06397bc09' and m.uuid=='afaf513ac1153755840e1d82b40e7d93'
 raw=Path(tempfile.mkdtemp(prefix='canvas-scene-removal-raw-',dir='/private/tmp'));ranges=[]
 for a,b,label in [(0x189dc,0x18bdc,'workspace'),(0x579fc,0x57d7c,'editor'),(0x5e2b0,0x5e354,'predicate'),(0x62da4,0x62dc4,'forwarder'),(0x1cbb4,0x1cc7c,'clear'),(0x61f68,0x6204c,'setter')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(raw/(label+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'name':label,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 calls=[]
 expected={0x18a68:'WorkspaceSceneC06editorB0',0x18b6c:'_$s22PreviewsFoundationHost3RefV8instancexvg',0x18b78:'EditorSceneC6update23forRemovedFileLocations',0x57a44:'PinningStateVMa',0x57ac4:'_$s16PreviewsPipeline11PreviewFileVMa',0x57ad4:'_$sSqMa',0x57b34:'_$sSqMa',0x57c1c:'_$s16PreviewsPipeline11PreviewFileV18previewDescriptionxvg',0x57c40:'_$s16PreviewsPipeline22PreviewFileDescriptionP8location8LocationQzSgvgTj',0x57ce8:'_$sSTsE8contains5whereS2b7ElementQzKXE_tKF',0x57d2c:'PinningStateV5clearyyF',0x57d38:'EditorSceneC12pinningState',0x5e330:'_$sSQ2eeoiySbx_xtFZTj',0x62db4:'EditorSceneC6update23forRemovedFileLocations',0x1cbdc:'_$s16PreviewsPipeline11PreviewFileVMa',0x1cbec:'_$sSqMa',0x1cc30:'PinningStateV6SourceOMa',0x1cc54:'_$sShMa',0x1cc64:'_$sSh9removeAll15keepingCapacityySb_tF',0x62020:'EditorSceneC12pinningState'}
 for a,name in expected.items():
  t=m.resolve(m.branch(a));names=[t['name']] if t['kind']=='import_stub' else t['names'];assert any(name in s for s in names),(hex(a),t);calls.append({'call':hex(a),'target':t})
 def fields(base):
  kind,size,count=struct.unpack('<HHI',m.read(base+8,8));assert size==12
  names=[]
  for i in range(count):
   a=base+16+i*size;dest=a+8+struct.unpack('<i',m.read(a+8,4))[0];names.append(m.read(dest,120).split(b'\0',1)[0].decode())
  return kind,names
 kind,pin_fields=fields(0x8c26c);assert kind==0 and pin_fields==['file','sources']
 kind,editor_fields=fields(0x8c5a0);assert kind==1 and len(editor_fields)==25 and editor_fields[8]=='pinningState'
 imports={}
 for a,name in [(0x963c0,'_$s16PreviewsPipeline22PreviewFileDescriptionTL'),(0x96658,'_$s8Location16PreviewsPipeline22PreviewFileDescriptionPTl'),(0x963a8,'_$s16PreviewsPipeline22PreviewFileDescriptionP8LocationAC_SHTn')]:
  s=next(s for s in m.sections if s['vm']<=a<s['vm']+s['length']);assert s['flags']&255==6
  actual=m.symbols[m.indirect[s['r1']+(a-s['vm'])//8]];assert actual==name;imports[hex(a)]=actual
 # Optional nil tests, contains branch, pinning field shared by reader/setter,
 # source-set clearing argument, and final didSet invocation.
 ops={0x57b90:0xf940539c,0x57bd0:0x52800021,0x57bdc:0x7100041f,0x57be0:0x54000181,0x57c60:0x52800021,0x57c6c:0x7100041f,0x57c70:0x540000a1,0x57cec:0x36000300,0x57cd0:0xf0000040,0x57cd4:0x91369000,0x5e334:0x12000000,0x61fc0:0xf94052f7,0x62000:0xf9400f08,0x1cc10:0x52800021,0x1cc14:0x52800022,0x1cc20:0xb9802677,0x1cc60:0x52800000}
 for a,v in ops.items():assert m.word(a)==v,hex(a)
 result={'image':{'sha256':hashlib.sha256(m.data).hexdigest(),'uuid':m.uuid,'architecture':'arm64'},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'calls':calls,'associated_location_imports':imports,'field_metadata':{'PinningState':pin_fields,'EditorScene_pinningState_index':8,'EditorScene_field_count':25},'source_policy':{'workspace':'Iterate the editorScenes Set of Ref<EditorScene>; obtain each Ref.instance and call its update(forRemovedFileLocations:) with the same array. Set enumeration order is not a semantic ordering guarantee.','editor_guards':'Read pinningState.file. Missing pinned PreviewFile or absent previewDescription.location exits after local cleanup without this clear/setter path.','match':'Use removed-location array contains(where:) with the recovered closure, which calls generic Equatable equality for the associated Location. No path-prefix or URL normalization semantics established.','matched':'When contains is true, copy current pinningState, call PinningState.clear and assign through the actual pinningState setter. False exits after local cleanup.','clear':'Destroy previous optional PreviewFile and write none; sources Set.removeAll(keepingCapacity:false). This is state-value cleanup, not proof of PreviewFile instance deinit or OS/transport resource settlement.','setter':'Copy old value, assign new pinningState using value witnesses, invoke pinningState.didSet, then destroy saved old state. didSet implementation and its downstream side effects are not qualified in this unit.','scope':'Source call chain and state cleanup only. No row destruction, renderer/session termination, resource release timing or runtime event execution established.'},'scope':{'static_only':True,'private_native_calls':0,'native_removed_event_observed':False,'pinning_didset_effects_qualified':False,'previewfile_deinit_or_resource_settlement_observed':False,'full_canvas_parity':False},'inherited_native_access_limitation':'Prior read-only native observe reported locked screen/empty Accessibility tree. No unchanged retry or permission/system change in this unit.'}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls':len(calls)}))
