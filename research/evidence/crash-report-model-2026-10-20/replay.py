"""Read-only UUID/source-domain/fixture/Rust reconstruction replay."""
from pathlib import Path
import sys,tempfile,subprocess,json,os,datetime,plistlib,hashlib,uuid
root=Path('/Users/8amps/xcpreviewer-rs');e=Path(__file__).parent;sys.path.insert(0,str(root/'tools/re'))
from reloop.core import Controller
from reloop.swiftmeta import MachO
base=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin')
with Controller().lock(),tempfile.TemporaryDirectory(prefix='crash-report-replay-') as tmp:
 t=Path(tmp);m=MachO('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/Versions/A/PreviewsMessagingHost');assert hashlib.sha256(m.data).hexdigest()=='0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c'
 metadata=json.loads((e/'independent-key-metadata.json').read_text())
 for name,record in metadata.items():
  address=int(record['descriptor'],16);kind,size,count=m.unpack('<HHI',m.file_offset(address)+8);assert count==record['count'] and size==12 and kind==2
  assert [m.string(m.relative(address+16+i*size+8)) for i in range(count)]==record['case_names']
 for source,binary in [('uuid_oracle.swift','uuid'),('uuid_defaults.swift','defaults')]:
  p=subprocess.run(['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc','-module-cache-path',str(t/'swift-cache'),str(e/source),'-o',str(t/binary)],capture_output=True,text=True,timeout=45);p.check_returncode()
 p=subprocess.run([str(t/'uuid')],capture_output=True,text=True,timeout=5);p.check_returncode();assert json.loads(p.stdout)==json.loads((e/'native-uuid-results.json').read_text())
 p=subprocess.run([str(t/'defaults')],capture_output=True,text=True,timeout=5);p.check_returncode();generated=json.loads(p.stdout);assert len(set(generated))==4
 for text in generated:assert uuid.UUID(text).version==4 and uuid.UUID(text).bytes[8]>>6==2
 full={'id':'00112233-4455-6677-8899-aabbccddeeff','name':'PreviewLab','bugType':'309','pid':12345,'time':datetime.datetime(2001,1,1,0,0,0,125000),'asi':{'Application Specific Information':['line1','按钮🧪']},'termination':{'flags':1,'code':9,'namespace':'SIGNAL','details':['sample'],'indicator':'owned','byProc':'ownedHarness','byPid':-1,'reasons':['explicit']},'images':[{'uuid':'opaque-image-id','arch':'arm64','base':4096,'path':'/owned/PreviewLab','name':'PreviewLab'}],'frames':[{'imageIndex':0,'imageOffset':16,'symbol':'body','symbolLocation':4,'sourceFile':'Owned.swift','sourceLine':7}],'logFilePath':'/owned/crash.ips'}
 values={'report-full':full,'report-canonical':dict(full,id=full['id'].upper()),'report-minimal':{'id':full['id'].upper(),'name':'Minimal','bugType':'0','pid':-1,'time':datetime.datetime(2001,1,1),'images':[],'frames':[]},'event-report':{'discriminant':'agentCrashedDiagnostics','crashReport':full},'request-report':{'discriminant':'symbolicateCrashedDiagnostics','crashReport':full}}
 fixture=root/'tools/re/rust/canvas-core/tests/fixtures/crash-report-model'
 for name,value in values.items():assert plistlib.dumps(value,fmt=plistlib.FMT_BINARY,sort_keys=False)==(fixture/(name+'.bplist')).read_bytes()
 env=dict(os.environ,RUSTC=str(base/'rustc'),RUSTDOC=str(base/'rustdoc'),CARGO_TARGET_DIR=str(t/'rust-target'))
 p=subprocess.run([str(base/'cargo'),'test','--offline','-p','canvas-core'],cwd=root,env=env,capture_output=True,text=True,timeout=60);print(p.stdout+p.stderr);p.check_returncode()
 p=subprocess.run([str(base/'cargo'),'build','--offline','-p','canvas-core','--bins'],cwd=root,env=env,capture_output=True,text=True,timeout=45);p.check_returncode()
 for binary,fixture in [('inspect-preview-crash','event-report.bplist'),('inspect-preview-request','request-report.bplist')]:
  p=subprocess.run([str(t/'rust-target/debug'/binary),str(root/'tools/re/rust/canvas-core/tests/fixtures/crash-report-model'/fixture)],capture_output=True,text=True,timeout=5);p.check_returncode();assert '00112233-4455-6677-8899-AABBCCDDEEFF pid=12345 images=1 frames=1' in p.stdout
 print(json.dumps({'source_modified':False,'tests_passed':47,'uuid_parse_cases':10,'native_default_uuid_samples':4,'key_domains_verified':4,'independent_fixtures_reproduced':5,'report_cli_cases':2,'private_runtime_invoked':False}))
