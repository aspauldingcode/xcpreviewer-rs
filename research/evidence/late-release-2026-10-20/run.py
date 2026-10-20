from pathlib import Path
import subprocess,resource,sys
w=Path(__file__).parent;out=Path(sys.argv[1]);out.mkdir(exist_ok=False);resource.setrlimit(resource.RLIMIT_CORE,(0,0))
for name,cmd in [('trace',['/usr/bin/clang','-Wall','-Wextra','-Werror','-dynamiclib','-lbsm',str(w/'trace.c'),'-install_name','@rpath/libtrace.dylib','-o',str(out/'libtrace.dylib')]),('oracle',['/usr/bin/clang','-Wall','-Wextra','-Werror','-fblocks',str(w/'oracle.m'),'-framework','Foundation','-L'+str(out),'-ltrace','-Wl,-rpath,@executable_path','-o',str(out/'oracle')])]:
 p=subprocess.run(cmd,capture_output=True,timeout=30);(out/(name+'.build')).write_bytes(p.stdout+p.stderr);p.check_returncode()
import os
for mode,withhold,late in [('withheld',True,False),('peer-loss-withheld',True,False),('peer-loss-late',True,True)]:
 env=os.environ.copy()
 for key in ['OWNED_INVOCATION_HOLDOUT','OWNED_INVOCATION_REPLY_ERROR','OWNED_INVOCATION_WRONG_SLOT','OWNED_PENDING_WITHHOLD','OWNED_PENDING_LATE_REPLY','OWNED_PEER_CANCEL']:env.pop(key,None)
 if mode.startswith('peer-loss'):env['OWNED_PEER_CANCEL']='1'
 if withhold:env['OWNED_PENDING_WITHHOLD']='1'
 if late:env['OWNED_PENDING_LATE_REPLY']='1'
 p=subprocess.run([str(out/'oracle'),'configured'],capture_output=True,timeout=5,env=env);(out/(mode+'.json')).write_bytes(p.stdout);(out/(mode+'.stderr')).write_bytes(p.stderr);print(mode,p.returncode,flush=True);p.check_returncode()
