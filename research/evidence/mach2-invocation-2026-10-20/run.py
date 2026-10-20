from pathlib import Path
import subprocess,resource,sys
w=Path(__file__).parent;out=Path(sys.argv[1]);out.mkdir(exist_ok=False);resource.setrlimit(resource.RLIMIT_CORE,(0,0))
for name,cmd in [('trace',['/usr/bin/clang','-Wall','-Wextra','-Werror','-dynamiclib','-lbsm',str(w/'trace.c'),'-install_name','@rpath/libtrace.dylib','-o',str(out/'libtrace.dylib')]),('oracle',['/usr/bin/clang','-Wall','-Wextra','-Werror','-fblocks',str(w/'oracle.m'),'-framework','Foundation','-L'+str(out),'-ltrace','-Wl,-rpath,@executable_path','-o',str(out/'oracle')])]:
 p=subprocess.run(cmd,capture_output=True,timeout=30);(out/(name+'.build')).write_bytes(p.stdout+p.stderr);p.check_returncode()
import os
for mode in ['primary','holdout','error-primary','error-holdout','wrong-slot']:
 env=os.environ.copy()
 if mode=='wrong-slot':env['OWNED_INVOCATION_WRONG_SLOT']='1'
 else:env.pop('OWNED_INVOCATION_WRONG_SLOT',None)
 if mode.startswith('error-')or mode=='wrong-slot':env['OWNED_INVOCATION_REPLY_ERROR']='1'
 else:env.pop('OWNED_INVOCATION_REPLY_ERROR',None)
 if mode.endswith('holdout'):env['OWNED_INVOCATION_HOLDOUT']='1'
 else:env.pop('OWNED_INVOCATION_HOLDOUT',None)
 p=subprocess.run([str(out/'oracle'),'configured'],capture_output=True,timeout=5,env=env);(out/(mode+'.json')).write_bytes(p.stdout);(out/(mode+'.stderr')).write_bytes(p.stderr);print(mode,p.returncode,flush=True);p.check_returncode()
