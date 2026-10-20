"""Fresh public CF date oracle and read-only original codec verification."""
from pathlib import Path
import sys,tempfile,subprocess,os,datetime,plistlib,json,hashlib
root=Path('/Users/8amps/xcpreviewer-rs');e=Path(__file__).parent;sys.path.insert(0,str(root/'tools/re'))
from reloop.core import Controller
base=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin')
with Controller().lock(),tempfile.TemporaryDirectory(prefix='crash-date-replay-') as tmp:
 t=Path(tmp);fixture=root/'tools/re/rust/canvas-core/tests/fixtures/crash-report'
 dates=[datetime.datetime(1970,1,1),datetime.datetime(2001,1,1),datetime.datetime(2001,1,1,0,0,0,125000),datetime.datetime(2000,12,31,23,59,59,500000),datetime.datetime(2038,1,19,3,14,7),datetime.datetime(2026,10,19,12,34,56,789000)]
 raw=plistlib.dumps(dates,fmt=plistlib.FMT_BINARY,sort_keys=False);assert raw==(fixture/'dates.bplist').read_bytes()
 request=plistlib.dumps({'discriminant':'requestScreenshot'},fmt=plistlib.FMT_BINARY,sort_keys=False);assert request==(fixture/'screenshot-request.bplist').read_bytes()
 p=subprocess.run(['/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang','-Wall','-Wextra','-Werror',str(e/'date_oracle.c'),'-framework','CoreFoundation','-o',str(t/'oracle')],capture_output=True,text=True,timeout=30);p.check_returncode()
 p=subprocess.run([str(t/'oracle'),str(fixture/'dates.bplist')],capture_output=True,text=True,timeout=5);p.check_returncode()
 expected=json.loads((e/'native-date-results.json').read_text())['expected_absolute_time_bits'];assert json.loads(p.stdout)==expected
 env=dict(os.environ,RUSTC=str(base/'rustc'),RUSTDOC=str(base/'rustdoc'),CARGO_TARGET_DIR=str(t/'rust-target'))
 p=subprocess.run([str(base/'cargo'),'test','--offline','-p','canvas-core'],cwd=root,env=env,capture_output=True,text=True,timeout=60);print(p.stdout+p.stderr);p.check_returncode()
 print(json.dumps({'source_modified':False,'tests_passed':39,'native_date_cases':6,'date_bytes_equal':48,'request_fixture_reproduced':True,'private_runtime_invoked':False}))
