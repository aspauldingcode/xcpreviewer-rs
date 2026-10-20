from pathlib import Path
import subprocess,resource,sys,json,os
w=Path(__file__).parent;out=Path(sys.argv[1]);out.mkdir(exist_ok=False);resource.setrlimit(resource.RLIMIT_CORE,(0,0))
for name,cmd in [('trace',['/usr/bin/clang','-Wall','-Wextra','-Werror','-dynamiclib','-lbsm',str(w/'trace.c'),'-install_name','@rpath/libtrace.dylib','-o',str(out/'libtrace.dylib')]),('oracle',['/usr/bin/clang','-Wall','-Wextra','-Werror','-Wno-error=deprecated-declarations','-fblocks',str(w/'oracle.m'),str(w/'peer.c'),'-I'+str(w),'-framework','Foundation','-lbsm','-L'+str(out),'-ltrace','-Wl,-rpath,@executable_path','-o',str(out/'oracle')])]:
 p=subprocess.run(cmd,capture_output=True,timeout=30);(out/(name+'.build')).write_bytes(p.stdout+p.stderr);p.check_returncode()
for mode in ['native','native-alias']:
 d=out/mode;d.mkdir();p=subprocess.run([str(out/'oracle'),mode,str(d)],capture_output=True,timeout=8);(d/'parent.json').write_bytes(p.stdout);(d/'stderr.log').write_bytes(p.stderr);print(mode,p.returncode,flush=True);p.check_returncode()
# Native wire is extracted locally; no private packet fixture is published.
import base64,struct
t='/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin';buildenv=os.environ.copy();buildenv.update(RUSTC=t+'/rustc',RUSTDOC=t+'/rustdoc',CARGO_TARGET_DIR='/private/tmp/scene-reply-20261020/target')
p=subprocess.run([t+'/cargo','build','--offline','-p','canvas-core','--bin','reencode-xpc-attachments'],cwd='/Users/8amps/xcpreviewer-rs/tools/re/rust',env=buildenv,capture_output=True,timeout=60);(out/'portable-build.log').write_bytes(p.stdout+p.stderr);p.check_returncode()
for mode in ['native','native-alias']:
 child=json.loads((out/mode/'child.json').read_text())[0];row=next(x for x in child['trace']if x['send_id']==0x20000000 and x['result']==0);body=base64.b64decode(row['send_body']);assert struct.unpack_from('<I',body)[0]==2
 (out/(mode+'-wire.bin')).write_bytes(body[28:])
 cli='/private/tmp/scene-reply-20261020/target/debug/reencode-xpc-attachments'
 p=subprocess.run([cli,str(out/(mode+'-wire.bin')),'2',str(out/(mode+'-portable.bin')),str(out/(mode+'-order.txt'))],capture_output=True,timeout=5);p.check_returncode()
for case,source,correct in [('portable','native',True),('portable-alias','native-alias',True),('wrong-order','native',False)]:
 d=out/case;d.mkdir();env=os.environ.copy();env['OWNED_XPC_CANDIDATE']=str(out/(source+'-portable.bin'))
 if correct:env['OWNED_XPC_ORDER']=str(out/(source+'-order.txt'))
 else:env.pop('OWNED_XPC_ORDER',None)
 p=subprocess.run([str(out/'oracle'),source,str(d)],env=env,capture_output=True,timeout=8);(d/'parent.json').write_bytes(p.stdout);(d/'stderr.log').write_bytes(p.stderr);print(case,p.returncode,flush=True);p.check_returncode()
buildenv['XCPREVIEW_NATIVE_FD_BODIES']=str(out/'native-wire.bin')+':'+str(out/'native-alias-wire.bin')
p=subprocess.run([t+'/cargo','test','--offline','-p','canvas-core','--test','xpc_descriptors','--','--nocapture'],cwd='/Users/8amps/xcpreviewer-rs/tools/re/rust',env=buildenv,capture_output=True,timeout=60);(out/'portable-tests.log').write_bytes(p.stdout+p.stderr);p.check_returncode()
p=subprocess.run(['python3',str(w/'verify.py'),str(out)],capture_output=True,timeout=10);(out/'verification.json').write_bytes(p.stdout);(out/'verification.stderr').write_bytes(p.stderr);p.check_returncode();print(p.stdout.decode())
