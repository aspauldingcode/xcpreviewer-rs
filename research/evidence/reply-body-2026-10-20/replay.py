"""Fresh owned native input -> portable re-encode -> native acceptance."""
from pathlib import Path
import subprocess,sys,resource,shutil,json,base64,os
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'));from reloop.core import Controller
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with Controller().lock():
 out=Path(sys.argv[1]).resolve();assert str(out).startswith(str(r/'research/raw')+'/') or str(out).startswith('/private/tmp/');out.mkdir(exist_ok=False,parents=True)
 for n in ['oracle.m','trace.c','trace.h']:shutil.copyfile(w/n,out/n)
 commands={'trace':['/usr/bin/clang','-Wall','-Wextra','-Werror','-dynamiclib',str(out/'trace.c'),'-install_name','@rpath/libtrace.dylib','-o',str(out/'libtrace.dylib')],'oracle':['/usr/bin/clang','-Wall','-Wextra','-Werror','-fblocks',str(out/'oracle.m'),'-framework','Foundation','-L'+str(out),'-ltrace','-Wl,-rpath,@executable_path','-o',str(out/'oracle')]}
 for name,cmd in commands.items():
  p=subprocess.run(cmd,capture_output=True,timeout=30);(out/(name+'.build')).write_bytes(p.stdout+p.stderr);p.check_returncode()
 for mode,name in [('native','body'),('native-holdout','holdout-body')]:
  p=subprocess.run([str(out/'oracle'),mode],capture_output=True,timeout=5);p.check_returncode();(out/(mode+'.stdout')).write_bytes(p.stdout);(out/(mode+'.stderr')).write_bytes(p.stderr);v=json.loads(p.stdout)[0];assert v['callback_payload_matches'];send=next(x for x in v['trace'] if x['send_id']==536870912 and x['result']==0);(out/(name+'.bin')).write_bytes(base64.b64decode(send['send_body']))
 tool='/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin';e=os.environ.copy();e.update(RUSTC=tool+'/rustc',RUSTDOC=tool+'/rustdoc',CARGO_TARGET_DIR='/private/tmp/scene-reply-20261020/target',XCPREVIEW_NATIVE_XPC_BODIES=str(out/'body.bin')+':'+str(out/'holdout-body.bin'))
 for args,log in [(['build','--offline','-p','canvas-core','--bin','reencode-xpc-body'],'portable-build.log'),(['test','--offline','-p','canvas-core','--test','xpc_wire','--','--nocapture'],'portable-tests.log')]:
  p=subprocess.run([tool+'/cargo',*args],cwd=r/'tools/re/rust',env=e,capture_output=True,timeout=60);(out/log).write_bytes(p.stdout+p.stderr);p.check_returncode()
 for mode,name in [('native','body'),('native-holdout','holdout-body')]:
  p=subprocess.run(['/private/tmp/scene-reply-20261020/target/debug/reencode-xpc-body',str(out/(name+'.bin')),str(out/(name+'-portable.bin'))],capture_output=True,timeout=5);p.check_returncode()
  p=subprocess.run([str(out/'oracle'),mode,str(out/(name+'-portable.bin'))],capture_output=True,timeout=5);(out/(name+'-portable.stdout')).write_bytes(p.stdout);(out/(name+'-portable.stderr')).write_bytes(p.stderr);p.check_returncode()
 p=subprocess.run(['python3',str(w/'verify.py'),str(out)],capture_output=True,timeout=10);(out/'verification.json').write_bytes(p.stdout);(out/'verification.stderr').write_bytes(p.stderr);p.check_returncode();print(p.stdout.decode())
