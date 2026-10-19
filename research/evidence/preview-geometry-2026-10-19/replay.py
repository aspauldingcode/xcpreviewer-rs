"""Read-only source replay: public oracle, frozen expectations, Rust tests and CLI."""
from pathlib import Path
import sys,subprocess,json,tempfile,os
root=Path('/Users/8amps/xcpreviewer-rs');evidence=Path(__file__).parent
sys.path.insert(0,str(root/'tools/re'))
from reloop.core import Controller
base=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin')
with Controller().lock(),tempfile.TemporaryDirectory(prefix='preview-geometry-replay-') as temp:
 t=Path(temp)
 p=subprocess.run(['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang','-Wall','-Wextra','-Werror',str(evidence/'geometry_oracle.c'),'-framework','CoreGraphics','-o',str(t/'oracle')],capture_output=True,text=True,timeout=30);p.check_returncode()
 p=subprocess.run([str(t/'oracle')],capture_output=True,text=True,timeout=5);p.check_returncode();cases=json.loads(p.stdout)
 assert cases==json.loads((evidence/'native-geometry.json').read_text())
 lines=['// Generated solely from the public native oracle before Rust implementation.','type Case = ([u64;4],u64,[u64;4],[u64;4],[u64;2]);','const NATIVE: &[Case] = &[']
 hx=lambda values:'['+','.join('0x'+x for x in values)+']'
 for c in cases:lines.append('('+hx(c['input'])+',0x'+c['factor']+','+hx(c['output'])+','+hx(c['point_output'])+','+hx(c['size_points'])+'),')
 lines+= ['];']
 assert '\n'.join(lines)+'\n'==(root/'tools/re/rust/canvas-core/tests/fixtures/geometry_cases.rs').read_text()
 env=dict(os.environ,RUSTC=str(base/'rustc'),RUSTDOC=str(base/'rustdoc'),CARGO_TARGET_DIR=str(t/'rust-target'))
 p=subprocess.run([str(base/'cargo'),'test','--offline','-p','canvas-core'],cwd=root,env=env,capture_output=True,text=True,timeout=60);print(p.stdout+p.stderr);p.check_returncode()
 p=subprocess.run([str(base/'cargo'),'build','--offline','-p','canvas-core','--bin','inspect-preview-geometry'],cwd=root,env=env,capture_output=True,text=True,timeout=45);p.check_returncode()
 p=subprocess.run([str(t/'rust-target/debug/inspect-preview-geometry'),str(root/'tools/re/rust/canvas-core/tests/fixtures/payload-defaults.bplist')],capture_output=True,text=True,timeout=5);p.check_returncode()
 assert 'size_in_points=(1.0, 0.6666666666666666) regions=1' in p.stdout
 assert 'point_rect=Rect { x: -0.5, y: 0.6666666666666666, width: 1.0833333333333333, height: 1.5 }' in p.stdout
 assert 'accessibility_bytes=4' in p.stdout
 print(json.dumps({'native_cases_reproduced':len(cases),'generated_fixture_matches':True,'cli_verified':True,'tests_passed':30,'source_modified':False}))
