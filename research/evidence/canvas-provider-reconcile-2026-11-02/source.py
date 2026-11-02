from pathlib import Path
import fcntl,hashlib,json,re,subprocess,tempfile
from macho import Image
here=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsScenes.framework/Versions/A/PreviewsScenes');m=Image(p)
 assert hashlib.sha256(m.data).hexdigest()=='e785b5947cd0ae70ff8977485f73f7181b6ed07c958ef29ce263ffa06397bc09' and m.uuid=='afaf513ac1153755840e1d82b40e7d93'
 raw=Path(tempfile.mkdtemp(prefix='canvas-provider-reconcile-raw-',dir='/private/tmp'));ranges=[]
 for a,b,label in [(0x3e4e0,0x3e890,'providers'),(0x3e890,0x3eb94,'preview-transform'),(0x47750,0x47758,'forwarder')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout;(raw/(label+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'name':label,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 expected={0x3e698:'ProviderSourceO2id',0x3e6c4:'IdentifiedSetVyxSg2IDQzcig',0x3e730:'ProviderV6source8isPinned',0x3e770:'ProviderV6source0A8Pipeline0E6SourceOvs',0x3e77c:'ProviderV8isPinnedSbvs',0x3e788:'ProviderV8previewsSayAC7PreviewVGvM',0x3e7b8:'transformElementsyyyxzXEF',0x3e9fc:'PreviewV4item',0x3ea54:'PreviewInstanceV08providerD0',0x3eb00:'ProviderPreviewInstanceV14providerSource',0x3eb0c:'PreviewInstanceV08providerC0',0x3eb2c:'PreviewV0A6ScenesE6update',0x3eb8c:'_diagnoseUnexpectedEnumCase'}
 calls=[]
 for a,name in expected.items():
  t=m.resolve(m.branch(a));names=[t['name']] if t['kind']=='import_stub' else t['names'];assert any(name in s for s in names),(hex(a),t);calls.append({'call':hex(a),'target':t})
 imports={}
 for a,name in [(0x95c98,'_$s16PreviewsPipeline14DiscoveredItemO7previewyAcA15PreviewInstanceVcACmFWC'),(0x95ca0,'_$s16PreviewsPipeline14DiscoveredItemO8registryyAC0A5Model18RegistryDefinitionVcACmFWC')]:
  sec=next(s for s in m.sections if s['vm']<=a<s['vm']+s['length']);assert sec['flags']&255==6
  actual=m.symbols[m.indirect[sec['r1']+(a-sec['vm'])//8]];assert actual==name;imports[hex(a)]=actual
 ops={0x3e63c:0xb4001193,0x3e6ec:0x7100041f,0x3e6f0:0x54000241,0x3e724:0x12000101,0x3e778:0x12000100,0x3e7b0:0xb0000040,0x3e7b4:0x911d4000,0x3e7c0:0x52800001,0x3e838:0xf1000673,0x3e844:0x54fff1e1,0x3ea14:0xf00002a8,0x3ea18:0xf9464d08,0x3ea24:0x54000421,0x3ea74:0x7100041f,0x3ea78:0x540002a1,0x3eaa4:0x14000030,0x3eaac:0xf9465108,0x3eab8:0x54000661,0x3eac8:0x14000026,0x3eb90:0xd4200020}
 for a,v in ops.items():assert m.word(a)==v,hex(a)
 assert m.branch(0x47754)==0x3e890
 result={'image':{'sha256':hashlib.sha256(m.data).hexdigest(),'uuid':m.uuid,'architecture':'arm64'},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'calls':calls,'enum_case_imports':imports,'source_policy':{'matching':'Iterate incoming ProviderSource array; obtain each source.id and look up optional existing DisplayableContent.Provider in captured IdentifiedSet.','miss':'Construct Provider(source:isPinned:) with current input source and low bit of supplied pinned flag.','hit':'Reuse matched provider value, assign current source and pinned flag, then transform the previews exposed after those setters. Whether setters also alter preview contents remains unqualified. Value reuse is not proof of object/session identity preservation.','preview_transform':'Read DiscoveredItem. Registry case returns after cleanup without this update path. Preview case with absent providerInstance likewise returns. Present providerInstance receives new providerSource, is wrapped into PreviewInstance.provider and DiscoveredItem.preview, then passed to Preview.update(withItem:). Unexpected case reaches native diagnostic/trap.','output':'Append one resulting provider per input source in input order; empty input returns empty array. Old entries not selected by input are not appended by this mapper. No explicit resource termination is inferred from exclusion.','boundaries':'Provider constructor/setter internals, Preview.update(withItem:) state/resource transitions, registry reconciliation, actual runtime reuse/removal and final settlement remain unqualified.'},'scope':{'static_only':True,'private_native_calls':0,'runtime_reuse_or_removal_observed':False,'preview_update_effects_qualified':False,'full_canvas_parity':False},'failures':['Exploratory branch decoder applied to the forwarder first instruction failed its B/BL assertion; actual branch is at 0x47754 and binds to 0x3e890. No control-flow inference from failed decode.','Registry helper explored separately but its complex item-refresh semantics are not qualified by this provider-only unit.','Prior locked-screen/Accessibility and Ghidra failures not retried unchanged.']}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls':len(calls)}))
