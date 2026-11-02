from pathlib import Path
import json,hashlib,struct,subprocess,re,tempfile,fcntl
from macho import Image
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;rawdir=Path(tempfile.mkdtemp(prefix='canvas-workspace-caller-raw-',dir='/private/tmp'))
p=Path('/Applications/Xcode.app/Contents/PlugIns/PreviewsXcode.framework/Versions/A/PreviewsXcode');digest='ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b'
with (r/'research/state/controller.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);m=Image(p);assert hashlib.sha256(m.data).hexdigest()==digest and m.uuid=='25c99c664185307188e31ab474573a10'
 ranges=[]
 for a,b,name in [(0x5d010,0x5d138,'entry'),(0x5d138,0x5d70c,'prepare-and-request'),(0x5d70c,0x5d760,'await-resume'),(0x5d760,0x5db14,'dependency-result'),(0x5db14,0x5dd68,'error-resume')]:
  out=subprocess.run(['xcrun','llvm-objdump','--arch=arm64','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p)],capture_output=True,timeout=20,check=True).stdout
  (rawdir/(name+'.raw.s')).write_bytes(out);words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',out.decode(),re.M)}
  assert set(words)==set(range(a,b,4));assert m.read(a,b-a)==b''.join(words[x] for x in range(a,b,4));ranges.append({'name':name,'start':hex(a),'end_exclusive':hex(b),'bytes':b-a,'sha256':hashlib.sha256(m.read(a,b-a)).hexdigest()})
 expected={0x5d134:'_swift_task_switch',0x5d338:'_swift_allocError',0x5d0dc:'_$sScM6sharedScMvgZ',0x5d254:'_objc_msgSend$isValid',0x5d260:'_objc_msgSend$buildSystemService',0x5d294:'_objc_msgSend$isValid',0x5d2c4:'_$s13PreviewsXcode0B16WorkspaceBuilderC24workspaceBuildParameters3forAA0bcfG0VSo17IDERunDestinationC_tKF',0x5d520:'_objc_msgSend$buildSystemService',0x5d598:'_swift_continuation_init',0x5d608:'_objc_msgSend$computeDependencyClosureForBuildables:buildParameters:includeImplicitDependencies:completionBlock:',0x5d62c:'_swift_continuation_await',0x5d320:'_$s13PreviewsXcode22WorkspaceNoLongerValid33_65BA9A005A9FF21AC987F9C3E9BD0579LLVADs5ErrorAAWl'}
 calls=[]
 for a,name in expected.items():
  row=m.resolve(m.branch(a));names=[row['name']] if row['kind']=='import_stub' else row['names'];assert name in names,(hex(a),names);calls.append({'call':hex(a),'target':row})
 fields=[]
 for a,name in [(0x38bd58,'_$s13PreviewsXcode0B16WorkspaceBuilderC19allSchemeBuildablesShyAA16BuildableWrapperVGvpWvd'),(0x38bd40,'_$s13PreviewsXcode0B16WorkspaceBuilderC11environmentAA0bC16BuildEnvironmentV9ValidatedVvpWvd'),(0x2b4a28,'_$s13PreviewsXcode0B16WorkspaceBuilderC9workspaceSo12IDEWorkspaceCvpWvd')]:assert name in m.named.get(a,[]);fields.append({'global_offset':hex(a),'name':name})
 assert struct.unpack('<Q',m.read(0x2b4a28,8))[0]==16
 v=m.word(0x5d600);assert v&0x7f800000==0x52800000 and v&31==4 and (v>>5)&65535==0
 # Validate the receiver argument position for the named workspace field.
 v=m.word(0x5d24c);assert v&31==26 and (v>>5)&31==20 and ((v>>10)&4095)*8==16
 result={'image':{'path':str(p),'sha256':digest,'uuid':m.uuid,'architecture':'arm64'},'source_bytes_verified':sum(x['bytes'] for x in ranges),'ranges':ranges,'calls':calls,'field_symbol_anchors':fields,'workspace_instance_field_offset':16,'dependency_request_include_implicit_dependencies':False,'scope':'Static source/metadata: cached scheme-buildable consumer, workspace/service validity branches, run-destination build parameters and continuation-based dependency request. Source of cached allSchemeBuildables and direct caller relationship to the earlier PreviewsIDEAPI policy remain untraced. No private native method or async ABI invoked.'}
 (w/'findings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_bytes_verified':result['source_bytes_verified'],'selected_calls_bound':len(calls)}))
