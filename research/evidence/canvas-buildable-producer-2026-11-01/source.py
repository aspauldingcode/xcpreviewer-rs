from pathlib import Path
import fcntl, hashlib, json, re, struct, subprocess, tempfile
from macho import Image
root=Path('/Users/8amps/xcpreviewer-rs'); here=Path(__file__).parent
image=Path('/Applications/Xcode.app/Contents/PlugIns/PreviewsXcode.framework/Versions/A/PreviewsXcode')
expected_digest='ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b'
with (root/'research/state/controller.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 m=Image(image)
 assert hashlib.sha256(m.data).hexdigest()==expected_digest
 assert m.uuid=='25c99c664185307188e31ab474573a10'
 a,b=0x24e884,0x24f63c
 raw=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image)],capture_output=True,check=True,timeout=20).stdout
 rawdir=Path(tempfile.mkdtemp(prefix='canvas-buildable-producer-raw-',dir='/private/tmp'))
 (rawdir/'make-builder.raw.s').write_bytes(raw)
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',raw.decode(),re.M)}
 assert set(words)==set(range(a,b,4))
 assert b''.join(words[x] for x in range(a,b,4))==m.read(a,b-a)
 assert '_$s13PreviewsXcode0B18WorkspaceSceneHostC11makeBuilderAA0bcG0CyKF' in m.named[a]
 expected={0x24eed0:'_objc_msgSend$runContextManager',0x24eef0:'_objc_msgSend$executionEnvironment',0x24ef28:'_$s14PreviewsIDEAPI11BuildSystemV10buildables6scheme9workspace17runContextManager20executionEnvironmentSaySo12IDEBuildable_pGSo9IDESchemeC_So12IDEWorkspaceCSo06IDERuniJ0CSo012IDEExecutionL0CtFZ',0x24efd8:'_$s22PreviewsFoundationHost3RefVyACyxGxcfC',0x24efe0:'_objc_msgSend$displayName',0x24f3b0:'_$sSl22PreviewsFoundationHostSH7ElementRpzrlE7uniquedShyACGyF',0x24f3d0:'_$s13PreviewsXcode0B16WorkspaceBuilderCMa',0x24f3dc:'_swift_allocObject'}
 calls=[]
 for address,name in expected.items():
  target=m.resolve(m.branch(address));names=[target['name']] if target['kind']=='import_stub' else target['names']
  assert name in names,(hex(address),names)
  calls.append({'call':hex(address),'target':target})
 field='_$s13PreviewsXcode0B16WorkspaceBuilderC19allSchemeBuildablesShyAA16BuildableWrapperVGvpWvd'
 assert field in m.named[0x38bd58]
 # Validate selected argument, result and cache-store register flow.
 def op(address,value):assert m.word(address)==value,hex(address)
 for address,value in {0x24ef18:0xaa1603e1,0x24ef1c:0xf9401e62,0x24ef24:0xaa0a03e3,0x24ef44:0xaa0003f8,0x24efac:0xaa1403e0,0x24efd0:0xaa1803e8,0x24efd4:0xaa1403e0,0x24f018:0xa900711b,0x24f054:0xaa1803e0,0x24f070:0x14000074,0x24f248:0x1400003d,0x24f33c:0xf9005e77,0x24f3a4:0x9102e274,0x24f3b4:0xf9005660,0x24f3e0:0xaa0003f7,0x24f544:0xf9405669,0x24f548:0xf8286ae9}.items():op(address,value)
 # ADRP x8 + ADD x8 + LDR x8 names the exact field-offset global.
 pc=0x24f538; v=m.word(pc); imm=(((v>>5)&0x7ffff)<<2)|((v>>29)&3)
 if imm&(1<<20):imm-=1<<21
 assert v&0x9f00001f==0x90000008
 page=(pc&~4095)+(imm<<12)
 v=m.word(pc+4);assert v&0xffc003ff==0x91000108
 assert page+((v>>10)&4095)==0x38bd58
 op(pc+8,0xf9400108)
 array_symbol=m.named.get(0x1e42e8,[])
 assert any('BuildableWrapper' in s for s in subprocess.run(['xcrun','swift-demangle'],input='\n'.join(array_symbol),text=True,capture_output=True,check=True,timeout=15).stdout.splitlines())
 result={'image':{'path':str(image),'sha256':expected_digest,'uuid':m.uuid,'architecture':'arm64'},'function':{'name':'XcodeWorkspaceSceneHost.makeBuilder','start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()},'source_bytes_verified':b-a,'calls':calls,'cache_field':{'global_offset':'0x38bd58','symbol':field,'set_result_spill':'0xa8','allocation_result_register':'x23','store_address':'0x24f548'},'source_inference':['makeBuilder obtains workspace runContextManager and executionEnvironment; passes scheme, workspace, manager and environment to BuildSystem.buildables.','Returned buildables are iterated, wrapped using FoundationHost.Ref and paired with displayName in BuildableWrapper storage.','Wrapper collection is uniqued to a set; result spills at scratch offset 0xa8 and is stored through the allSchemeBuildables field-offset global on the newly allocated XcodeWorkspaceBuilder.','This producer and the prior cached-consumer source establish the selection-to-dependency-request source chain; they do not establish an observed runtime invocation.'],'scope':{'static_source_only':True,'native_private_calls':0,'fresh_ui_observation':False,'runtime_preferences_observed':False,'runtime_chain_execution_observed':False,'milestone_parity_complete':False}}
 (here/'findings.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'source_bytes_verified':b-a,'selected_calls_bound':len(calls),'producer_cache_flow_verified':True}))
