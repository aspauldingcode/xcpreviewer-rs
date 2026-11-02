from pathlib import Path
import fcntl,hashlib,json,re,struct,subprocess,tempfile
from macho import Image
root=Path('/Users/8amps/xcpreviewer-rs');here=Path(__file__).parent
raw=Path(tempfile.mkdtemp(prefix='canvas-build-stop-raw-',dir='/private/tmp'))
with (root/'research/state/controller.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=Path('/Applications/Xcode.app/Contents/PlugIns/PreviewsXcode.framework/Versions/A/PreviewsXcode');m=Image(p)
 q=Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsPipeline.framework/Versions/A/PreviewsPipeline');n=Image(q)
 assert hashlib.sha256(m.data).hexdigest()=='ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b' and m.uuid=='25c99c664185307188e31ab474573a10'
 assert hashlib.sha256(n.data).hexdigest()=='c0897c050716f12f88da4dd08c24e3d3ae1de36dc748b65ad0b7346979e40053' and n.uuid=='c6ed2a5e6f2e3a41a1586d2f65e00a58'
 ranges=[]
 # Full inherited handler includes prologue payload preservation, dispatch, gates,
 # associated-value cleanup, common refresh continuation and shared return.
 a,b=0x248ef0,0x24a318
 out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout
 (raw/'handler.raw.s').write_bytes(out)
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([a-f0-9]+):\s*([a-f0-9]{8})\s',out.decode(),re.M)}
 assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
 ranges.append({'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 for a,fragment in [(0x36ceb8,'_shouldAutoResumeWhenC13BuildSucceeds'),(0x36cec0,'UserDefaultVySbGvpZ'),(0x38bf28,'workspaceD0'),(0x36cb58,'environmentCoalescer'),(0x36cb50,'lastC7Builder')]:assert any(fragment in x for x in m.named[a]),hex(a)
 calls=[]
 expected={0x2496c4:'_$s22PreviewsFoundationHost11UserDefaultV12wrappedValuexvg',0x249710:'_$s14PreviewsScenes14WorkspaceSceneC14previewService0A8Pipeline07PreviewF0Cvg',0x249730:'_$s16PreviewsPipeline14PreviewServiceC13buildingStateAA0b8BuildingF0Ovg',0x249748:'_swift_getEnumCaseMultiPayload',0x249760:'_$s16PreviewsPipeline20PreviewBlockedReasonOMa',0x24a218:'_$s13PreviewsXcode0B25BuildEnvironmentCoalescerC14setNeedsUpdateyyF',0x24a234:'_$s16PreviewsPipeline19PreviewUpdateReasonV20userRequestedRefreshACvgZ',0x24a24c:'_$s14PreviewsScenes14WorkspaceSceneC14setNeedsUpdate3fory0A8Pipeline07PreviewG6ReasonV_tF',0x248f24:'_$s16PreviewsPipeline0B13BuildingStateOMa',0x24a310:'_swift_once'}
 for a,name in expected.items():
  t=m.resolve(m.branch(a));names=[t['name']] if t['kind']=='import_stub' else t['names'];assert name in names,(hex(a),t);calls.append({'call':hex(a),'target':t})
 # Explicit source anchors, rather than inferred enum cases from instruction constants alone.
 ops={0x248f1c:0xaa0003fb,0x2493fc:0xf810011b,0x249514:0xf850011b,0x249664:0x7100111f,0x249668:0x540026c1,0x2496d8:0x385803a8,0x2496dc:0x0a1b0108,0x2496e0:0x36004d48,0x249704:0xb4004c34,0x24974c:0x51000808,0x249750:0x7100091f,0x249754:0x540049a3,0x249758:0x35005000,0x24977c:0x1400027c,0x24a228:0xf8286b3f,0x24a23c:0xb40000f4,0x24a314:0x17fffcdb}
 for a,v in ops.items():assert m.word(a)==v,hex(a)
 # Resolve the metadata pointer used by the enum-case runtime call via its prologue getter.
 assert m.word(0x248f28)==0xd10203a8 and m.word(0x248f2c)==0xf8100100
 assert m.word(0x249740)==0xd10203a8 and m.word(0x249744)==0xf8500101
 assert any('0B13BuildingStateOMF' in x for x in n.named[0x556d4c])
 base=0x556d4c;kind,size,count=struct.unpack('<HHI',n.read(base+8,8));assert (kind,size,count)==(2,12,4)
 payload_word,empty=struct.unpack('<II',n.read(0x562e28+20,8));assert payload_word&0xffffff==2 and empty==2
 cases=[]
 for i in range(count):
  a=base+16+i*size;dest=a+8+struct.unpack('<i',n.read(a+8,4))[0];name=n.read(dest,100).split(b'\0',1)[0].decode();has_payload=n.word(a+4)!=0
  cases.append({'logical_tag':i,'name':name,'has_payload':has_payload})
 assert [(x['name'],x['has_payload']) for x in cases]==[('blocked',True),('paused',True),('running',False),('empty',False)]
 # Interpret the checked SUB/CMP unsigned-low branch for every valid logical tag.
 state_routes=[]
 subtract=(m.word(0x24974c)>>10)&4095;comparison=(m.word(0x249750)>>10)&4095
 for c in cases:
  tag=c['logical_tag'];skip=((tag-subtract)&0xffffffff)<comparison
  state_routes.append({**c,'source_route':'return' if skip else 'refresh after associated-value cleanup'})
 assert [x['source_route']=='return' for x in state_routes]==[False,False,True,True]
 result={'images':{x.path.name:{'sha256':hashlib.sha256(x.data).hexdigest(),'uuid':x.uuid,'architecture':'arm64'} for x in [m,n]},'ranges':ranges,'instruction_bytes_reverified':5160,'selected_calls':calls,'building_state_metadata':{'field_descriptor':'0x556d4c','nominal_descriptor':'0x562e28','payload_cases':2,'empty_cases':2,'source_routes':state_routes},'source_policy':{'dispatch':'Logical event tag 4 follows build-stop route. Payload low bit comes from prior qualified listener result == 1 comparison.','preference':'Lazy UserDefault<Bool> _shouldAutoResumeWhenBuildSucceeds; effective default/value not observed. wrappedValue low bit AND stop payload low bit must be true.','scene':'Missing workspaceScene returns without refresh. Present scene supplies previewService.buildingState.','state':'running or empty returns. blocked or paused destroys associated state and continues; no particular pause/block reason comparison appears on this recovered route.','refresh':'Surviving path schedules environmentCoalescer, clears/releases cached lastWorkspaceBuilder, constructs userRequestedRefresh, and requests setNeedsUpdate on the scene if still present.','scope':'Request submission only. No immediate unpause, resumed rendering, preserved state, completed build or timing behavior established.'},'scope':{'static_only':True,'native_private_calls':0,'actual_build_stop_event_observed':False,'effective_preference_observed':False,'result_enum_name_known':False,'complete_refresh_or_canvas_parity':False}}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'bytes_reverified':5160,'selected_calls':len(calls),'building_states':len(cases)}))
