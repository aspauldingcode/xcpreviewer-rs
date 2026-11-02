from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;p=Path('/Applications/Xcode.app/Contents/PlugIns/PreviewsXcode.framework/Versions/A/PreviewsXcode')
with (r/'research/state/controller.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);m=Image(p);digest=hashlib.sha256(m.data).hexdigest()
 assert digest=='ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b' and m.uuid=='25c99c664185307188e31ab474573a10'
 rawdir=Path(tempfile.mkdtemp(prefix='canvas-workspace-events-raw-',dir='/private/tmp'));ranges=[]
 for a,b,n in [(0x248ef0,0x24a318,'handler'),(0x16cdd0,0x16cde8,'enum-tag')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout
  (rawdir/(n+'.raw.s')).write_bytes(out);words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'name':n,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 def op(a,v):assert m.word(a)==v,hex(a)
 assert any('handleC5Event' in n for n in m.named[0x248ef0])
 assert any('WorkspaceListenerC5EventOMF' in n for n in m.named[0x30a844])
 assert any('WorkspaceListenerC5EventOMn' in n for n in m.named[0x2e81c4])
 def rel(a):return a+struct.unpack('<i',m.read(a,4))[0]
 base=0x30a844;kind,size,count=struct.unpack('<HHI',m.read(base+8,8));assert (kind,size,count)==(3,12,11)
 assert struct.unpack('<II',m.read(0x2e81c4+20,8))==(5,6)
 cases=[]
 for i in range(count):
  a=base+16+size*i;name=m.read(rel(a+8),200).split(b'\0',1)[0].decode();has_type=m.word(a+4)!=0
  assert has_type==(i<5);cases.append({'reflection_order':i,'name':name,'associated_type_present':has_type})
 assert [x['name'] for x in cases]==['blueprintDidChange','modifiedFiles','removedFiles','buildSystemBuildStarted','buildSystemBuildStopped','workspaceSettingsChanged','newSchemeSelected','newRunDestinationSelected','didFinishPackageLoading','activeSchemeDidChange','installablePlatformsDidChange']
 # Tag witness: payload cases use byte 8 (0..4); empty cases use word 0 + 5.
 for a,v in {0x16cdd0:0xb9400008,0x16cdd4:0x39402009,0x16cdd8:0x11001508,0x16cddc:0x7100113f,0x16cde0:0x1a898100,0x16cde4:0xd65f03c0,0x2495c4:0x12001f88,0x2495c8:0x7100091f,0x2495d0:0x5400046c,0x24965c:0x71000d1f,0x249660:0x54000fe0,0x249664:0x7100111f,0x249668:0x540026c1}.items():op(a,v)
 # Interpret only the pinned empty-case comparison/conditional-branch dispatch.
 entries={0x249f64,0x249d2c,0x249b54,0x249fb4,0x249ff0}
 def signed(n,bits):return n-(1<<bits) if n&(1<<(bits-1)) else n
 def route(index):
  pc=0x249b40;comparison=None;visited=[]
  for _ in range(12):
   if pc in entries:return pc,visited
   visited.append(hex(pc));v=m.word(pc)
   if v&0xffc003ff==0xf100037f:comparison=index-((v>>10)&4095);pc+=4
   elif v&0xff000010==0x54000000:
    cond=v&15;assert cond in (0,1,12);take={0:comparison==0,1:comparison!=0,12:comparison>0}[cond];pc=pc+signed((v>>5)&0x7ffff,19)*4 if take else pc+4
   elif v&0xff00001f==0xb400001b:pc=pc+signed((v>>5)&0x7ffff,19)*4 if index==0 else pc+4
   else:raise AssertionError((hex(pc),hex(v)))
  raise AssertionError('dispatch bound')
 expected_entries=[0x249f64,0x249d2c,0x249b54,0x249fb4,0x249d2c,0x249ff0]
 call_for={0x249f64:0x249f70,0x249d2c:0x249d38,0x249b54:0x249b60,0x249fb4:0x249fc0,0x249ff0:0x249ffc}
 rows=[];calls=[]
 for i,case in enumerate(cases[5:]):
  entry,visited=route(i);assert entry==expected_entries[i]
  call=call_for[entry];t=m.resolve(m.branch(call));assert any('CoalescerC14setNeedsUpdateyyF' in n for n in t['names'])
  # Each entry loads environmentCoalescer at 36cb58, then clears lastWorkspaceBuilder at 36cb50.
  op(entry+4,0xf945ad08);op(entry+8,0xf8686b34);op(entry+16,0xf0000908 if entry!=0x249ff0 else 0xd0000908);op(entry+20,0xf945a908);op(entry+24,0xf8686b20);op(entry+28,0xf8286b3f)
  rows.append({'event':case['name'],'empty_case_payload_word':i,'logical_tag':i+5,'handler_entry':hex(entry),'dispatch_visited':visited,'coalescer_call':hex(call),'cache_clear':hex(entry+28),'scene_reason':'previewsChanged' if i==2 else 'workspaceChanged','reason_text':None if i==2 else ('Workspace build settings changed' if i==0 else 'Current scheme changed')})
  if call not in [int(c['call'],16) for c in calls]:calls.append({'call':hex(call),'target':t})
 for a,name in [(0x249b84,'_$s16PreviewsPipeline19PreviewUpdateReasonV15previewsChangedACvgZ'),(0x24a038,'_$s16PreviewsPipeline19PreviewUpdateReasonV16workspaceChangedyACSSFZ'),(0x24a06c,'_$s14PreviewsScenes14WorkspaceSceneC14setNeedsUpdate3fory0A8Pipeline07PreviewG6ReasonV_tF')]:
  t=m.resolve(m.branch(a));assert t['name']==name;calls.append({'call':hex(a),'target':t})
 for a,text in [(0x2d8ee0,'Workspace build settings changed'),(0x2d8f30,'Current scheme changed')]:assert m.read(a,len(text)+1)==text.encode()+b'\0'
 for a,part in [(0x36cb50,'lastC7Builder'),(0x36cb58,'environmentCoalescer')]:assert any(part in n for n in m.named[a])
 result={'image':{'path':str(p),'sha256':digest,'uuid':m.uuid,'architecture':'arm64'},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'enum_metadata':{'field_descriptor':'0x30a844','nominal_descriptor':'0x2e81c4','payload_cases':5,'empty_cases':6,'cases':cases},'empty_event_routes':rows,'calls':calls,'source_inference':'All six valid payload-free listener events schedule the environment coalescer, clear/release the cached builder, and request a scene update. Destination selection uses previewsChanged; other recovered empty events use workspaceChanged. Logical event tags are derived from pinned reflection, enum counts, tag witness and interpreted handler comparisons, not native invocation.','scope':{'static_only':True,'private_native_calls':0,'fresh_ui_observation':False,'payload_event_behaviors_recovered':False,'complete_event_mapping':False,'runtime_event_delivery_observed':False,'full_canvas_parity':False}}
 (w/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'empty_event_routes':len(rows),'selected_call_bindings':len(calls)}))
