"""Owned descriptor capture -> portable binding plan -> native acceptance."""
from pathlib import Path
import subprocess,sys,resource,shutil,json,base64,struct,os
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'tools/re'));from reloop.core import Controller
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with Controller().lock():
 out=Path(sys.argv[1]).resolve();assert str(out).startswith(str(r/'research/raw')+'/') or str(out).startswith('/private/tmp/');out.mkdir(exist_ok=False,parents=True)
 for n in ['oracle.m','trace.c','trace.h']:shutil.copyfile(w/n,out/n)
 for name,cmd in [('trace',['/usr/bin/clang','-Wall','-Wextra','-Werror','-dynamiclib',str(out/'trace.c'),'-install_name','@rpath/libtrace.dylib','-o',str(out/'libtrace.dylib')]),('oracle',['/usr/bin/clang','-Wall','-Wextra','-Werror','-fblocks',str(out/'oracle.m'),'-framework','Foundation','-L'+str(out),'-ltrace','-Wl,-rpath,@executable_path','-o',str(out/'oracle')])]:
  p=subprocess.run(cmd,capture_output=True,timeout=30);(out/(name+'.build')).write_bytes(p.stdout+p.stderr);p.check_returncode()
 for mode in ['native','native-alias']:
  p=subprocess.run([str(out/'oracle'),mode],capture_output=True,timeout=5);p.check_returncode();(out/(mode+'.stdout')).write_bytes(p.stdout);(out/(mode+'.stderr')).write_bytes(p.stderr);v=json.loads(p.stdout)[0];send=next(t for t in v['trace']if t['send_id']==536870912 and t['result']==0);b=base64.b64decode(send['send_body']);n=struct.unpack_from('<I',b)[0];assert n==2;(out/(mode+'-wire.bin')).write_bytes(b[4+12*n:])
 t='/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin';e=os.environ.copy();e.update(RUSTC=t+'/rustc',RUSTDOC=t+'/rustdoc',CARGO_TARGET_DIR='/private/tmp/scene-reply-20261020/target',XCPREVIEW_NATIVE_FD_BODIES=str(out/'native-wire.bin')+':'+str(out/'native-alias-wire.bin'))
 for args,log in [(['build','--offline','-p','canvas-core','--bin','reencode-xpc-attachments'],'portable-build.log'),(['test','--offline','-p','canvas-core','--test','xpc_descriptors','--','--nocapture'],'portable-tests.log')]:
  p=subprocess.run([t+'/cargo',*args],cwd=r/'tools/re/rust',env=e,capture_output=True,timeout=60);(out/log).write_bytes(p.stdout+p.stderr);p.check_returncode()
 for mode in ['native','native-alias']:
  p=subprocess.run(['/private/tmp/scene-reply-20261020/target/debug/reencode-xpc-attachments',str(out/(mode+'-wire.bin')),'2',str(out/(mode+'-portable.bin')),str(out/(mode+'-order.txt'))],capture_output=True,timeout=5);p.check_returncode()
 for mode in ['native','native-alias','native-wrong-order']:
  source='native-alias' if mode=='native-alias' else 'native';cmd=[str(out/'oracle'),mode,str(out/(source+'-portable.bin'))]
  if mode!='native-wrong-order':cmd.append(str(out/(source+'-order.txt')))
  p=subprocess.run(cmd,capture_output=True,timeout=5);(out/(mode+'-portable.stdout')).write_bytes(p.stdout);(out/(mode+'-portable.stderr')).write_bytes(p.stderr);p.check_returncode()
 p=subprocess.run(['python3',str(w/'verify.py'),str(out)],capture_output=True,timeout=10);(out/'verification.json').write_bytes(p.stdout);(out/'verification.stderr').write_bytes(p.stderr);p.check_returncode();print(p.stdout.decode())
