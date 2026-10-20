from pathlib import Path
import subprocess,resource,sys,os,platform
w=Path(__file__).parent;out=Path(sys.argv[1]);out.mkdir(exist_ok=False);resource.setrlimit(resource.RLIMIT_CORE,(0,0));assert platform.release()=='25.5.0'
for name,cmd in [('trace',['/usr/bin/clang','-Wall','-Wextra','-Werror','-dynamiclib','-lbsm',str(w/'trace.c'),'-install_name','@rpath/libtrace.dylib','-o',str(out/'libtrace.dylib')]),('oracle',['/usr/bin/clang','-Wall','-Wextra','-Werror','-fblocks',str(w/'oracle.m'),'-framework','Foundation','-L'+str(out),'-ltrace','-Wl,-rpath,@executable_path','-o',str(out/'oracle')])]:
 p=subprocess.run(cmd,capture_output=True,timeout=30);(out/(name+'.build')).write_bytes(p.stdout+p.stderr);p.check_returncode()
for mode,key,holdout,both in [('argument-primary','1',False,False),('reserved-error-primary','BSXPCReturnError',False,False),('reserved-error-holdout','BSXPCReturnError',True,False),('reserved-value-primary','BSXPCReturnValue',False,False),('combined-error-primary','BSXPCReturnError',False,True),('conflict-primary','BSXPCReturnError',False,True),('conflict-holdout','BSXPCReturnError',True,True)]:
 env=os.environ.copy()
 for k in ['OWNED_SERVICE_REPLY_CONFLICT','OWNED_INVOCATION_HOLDOUT','OWNED_INVOCATION_WRONG_SLOT','OWNED_SERVICE_REPLY_INCLUDE_NUMBERED']:env.pop(k,None)
 env['OWNED_INVOCATION_REPLY_ERROR']='1';env['OWNED_SERVICE_REPLY_KEY']=key
 if holdout:env['OWNED_INVOCATION_HOLDOUT']='1'
 if both:env['OWNED_SERVICE_REPLY_INCLUDE_NUMBERED']='1'
 if mode.startswith('conflict-'):env['OWNED_SERVICE_REPLY_CONFLICT']='1'
 p=subprocess.run([str(out/'oracle'),'configured'],capture_output=True,timeout=5,env=env);(out/(mode+'.json')).write_bytes(p.stdout);(out/(mode+'.stderr')).write_bytes(p.stderr);print(mode,p.returncode,flush=True);p.check_returncode()
