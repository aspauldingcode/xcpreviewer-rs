from pathlib import Path
import json,hashlib,fcntl,subprocess,tempfile,re
from macho import Image
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent
p=Path('/Applications/Xcode.app/Contents/PlugIns/PreviewsXcode.framework/Versions/A/PreviewsXcode')
with (r/'research/state/controller.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);m=Image(p)
 digest=hashlib.sha256(m.data).hexdigest();assert digest=='ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b' and m.uuid=='25c99c664185307188e31ab474573a10'
 rawdir=Path(tempfile.mkdtemp(prefix='canvas-builder-lifecycle-raw-',dir='/private/tmp'));ranges=[]
 for a,b,n in [(0x24e884,0x24f63c,'make-builder'),(0x4f3a4,0x4f700,'coalescer')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,check=True,timeout=20).stdout
  (rawdir/(n+'.raw.s')).write_bytes(out)
  words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4)) and b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
  ranges.append({'name':n,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 expected={0x24e9e0:'_$s13PreviewsXcode0B18WorkspaceSceneHostC24openOrPreviewedFilePaths33_79390B747E07F69D30A6D48DE90213E2LLShySo11DVTFilePathCGvg',0x24ea50:'_$s13PreviewsXcode0B25BuildEnvironmentCoalescerC14setNeedsUpdateyyF',0x24eb30:'_$s13PreviewsXcode0B25BuildEnvironmentCoalescerC7updatedAC12UpdateResultVyF',0x4f3c4:'_objc_msgSend$invalidate',0x4f530:'_objc_msgSend$isValid',0x4f53c:'_objc_msgSend$cancelScheduledInvocation',0x4f544:'_objc_msgSend$scheduleInvocation',0x4f618:'_objc_msgSend$hasScheduledInvocation',0x4f624:'_objc_msgSend$isInvoking'}
 calls=[]
 for a,name in expected.items():
  t=m.resolve(m.branch(a));names=[t['name']] if t['kind']=='import_stub' else t['names'];assert name in names,(hex(a),names)
  calls.append({'call':hex(a),'target':t})
 # Source identifiers and selected register/branch flow; generic demangler labels are not imported call identities.
 for a,part in [(0x36cb50,'lastC7Builder'),(0x36cb58,'environmentCoalescer'),(0x38bd98,'openAndPreviewedFilesAtCreation'),(0x35df38,'updateInvocation'),(0x38bd20,'lastUpdate'),(0x38bd28,'updateCallback'),(0x38bd30,'didUpdateCallback'),(0x38bd38,'queryManager')]:assert any(part in n for n in m.named.get(a,[])),hex(a)
 ops={0x24e9ec:0xf945a918,0x24e9f0:0xf8786a97,0x24e9fc:0xb4000377,0x24ea04:0x91366108,0x24ea08:0xf9400108,0x24ea0c:0xf8686af4,0x24ea20:0xaa1c03e1,0x24ea34:0x3600009a,0x24ea40:0x140000db,0x24ea60:0xf8386b5f,0x24edac:0xaa1703e0,0x24f5e8:0xf8286ae9,0x24f614:0xf9402669,0x24f61c:0xf8296917,0x4f3cc:0xf8336a9f,0x4f3f8:0xa9007e7f,0x4f410:0xa9007d1f,0x4f424:0xf8286a9f,0x4f524:0xb4000160,0x4f534:0x340000a0,0x4f60c:0xb4000520,0x4f61c:0x34000100,0x4f634:0x37000099,0x4f638:0x1400001e,0x4f694:0x54000141}
 for a,v in ops.items():assert m.word(a)==v,hex(a)
 t=m.resolve(m.branch(0x24ea24));assert any('Sh' in n and 'DVTFilePath' in n for n in t['names']);calls.append({'call':'0x24ea24','target':t})
 t=m.resolve(m.branch(0x4f6b4));assert any('Coalescer' in n and 'update' in n for n in t['names']);calls.append({'call':'0x4f6b4','target':t})
 result={'image':{'path':str(p),'sha256':digest,'uuid':m.uuid,'architecture':'arm64'},'ranges':ranges,'source_bytes_verified':sum(x['bytes'] for x in ranges),'new_coalescer_bytes':860,'previous_make_builder_bytes_reverified':3512,'calls':calls,'source_inference':{'cache_hit':'If lastWorkspaceBuilder exists and its openAndPreviewedFilesAtCreation equals current openOrPreviewedFilePaths, return retained existing builder before coalescer.updated or BuildSystem.buildables.','cache_miss':'Path-set mismatch calls coalescer.setNeedsUpdate, clears/releases lastWorkspaceBuilder, then enters update/rebuild path. Newly constructed builder stores the current path set and replaces the host cache.','coalescer_reschedule':'setNeedsUpdate checks optional delayed invocation validity, cancels scheduled invocation then schedules it. No delay duration inferred.','coalescer_updated':'Missing invocation, scheduled-but-not-invoking invocation, or missing lastUpdate enters update(); otherwise copies existing lastUpdate. No private ABI invoked to test scheduling or reentrancy.','coalescer_invalidate':'invalidate calls optional delayed invocation.invalidate and clears/releases invocation, didUpdateCallback, updateCallback and queryManager slots. Final resource disposal is unobserved.'},'scope':{'static_only':True,'native_runtime_calls':0,'fresh_ui_observation':False,'event_to_invalidation_mapping_complete':False,'native_cache_identity_observed':False,'exact_coalescing_delay_known':False,'full_canvas_parity':False}}
 (w/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'new_coalescer_bytes':860,'selected_calls_bound':len(calls)}))
