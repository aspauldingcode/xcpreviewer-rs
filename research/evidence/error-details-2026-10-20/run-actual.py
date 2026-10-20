from pathlib import Path
import subprocess,os,json,sys
w=Path(__file__).parent;out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
for name,cmd in [('trace',['/usr/bin/clang','-Wall','-Wextra','-Werror','-dynamiclib','-lbsm',str(w/'actual-trace.c'),'-install_name','@rpath/libtrace.dylib','-o',str(out/'libtrace.dylib')]),('actual',['/usr/bin/clang','-Wall','-Wextra','-Werror','-fblocks',str(w/'actual.m'),'-framework','Foundation','-L'+str(out),'-ltrace','-Wl,-rpath,@executable_path','-o',str(out/'actual')])]:
 p=subprocess.run(cmd,capture_output=True,timeout=30);(out/(name+'.build')).write_bytes(p.stdout+p.stderr);p.check_returncode()
env=os.environ.copy()
for k in ['OWNED_PEER_CANCEL','OWNED_PENDING_LATE_REPLY','OWNED_INVOCATION_HOLDOUT','OWNED_INVOCATION_REPLY_ERROR','OWNED_INVOCATION_WRONG_SLOT']:env.pop(k,None)
env['OWNED_PENDING_WITHHOLD']='1';p=subprocess.run([str(out/'actual'),'configured'],capture_output=True,timeout=5,env=env);(out/'native.json').write_bytes(p.stdout);(out/'native.stderr').write_bytes(p.stderr);p.check_returncode()
d=json.loads(p.stdout);assert d['boardservices_uuid_verified'] and d['baseboard_uuid_verified'] and d['action_completion_callbacks']==1 and d['observed_error_code']==3 and d['observed_error_domain']=='BSServiceConnectionErrorDomain' and d['factory_restored'] and d['factory_hits']==1
info={'BSErrorCodeDescription':'OperationFailed','NSLocalizedFailureReason':'XPC error received on message reply handler'};assert d['actual_user_info']==info
assert [x['offset']for x in d['factory_stack']if x['image']=='/System/Library/PrivateFrameworks/BoardServices.framework/Versions/A/BoardServices'][:3]==[432180,431340,363308] and d['factory_user_info']==info
b=bytes.fromhex(d['actual_archive_hex']);(out/'actual-diagnostic.archive').write_bytes(b);assert b==(w/'replay/corpus/diagnostic.archive').read_bytes();print(json.dumps({'actual_native_factory_error3_archive_bytes':len(b),'equal_independent_authored_field_control':True,'actual_native_callback':True,'new_archive_is_local_encoding_not_captured_error_reply':True}))
