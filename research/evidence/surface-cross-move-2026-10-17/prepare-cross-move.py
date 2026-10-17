from pathlib import Path
import json,hashlib
s=Path('/private/tmp/surface-cross-receive-20261017');d=Path('/private/tmp/surface-cross-move-20261017');d.mkdir(exist_ok=False)
for n in ['surface_ipc_probe.c','run_guard.js','execute.py','run_before_deadline.py','observed_compiler.js','observed_group_anchor.py','sdk-identity.json','environment.json','test_gate.py','pre-lock-only-execute.py','record_admit.py','verify-frozen.py']:
 t=(s/n).read_text()
 if n in ['execute.py','run_before_deadline.py','test_gate.py']:t=t.replace('17,41,7','17,51,7').replace('17:41:07','17:51:07')
 (d/n).write_text(t)
t=(s/'probe.c').read_text().replace('// Owned fork/exec receiver; fixed receive-size contrast and fresh resend.','// Paired COPY/MOVE initial descriptor; CF-held recovery after receive-size error.')
t=t.replace('unsigned id,uint32_t sid){struct transfer','unsigned id,uint32_t sid,int move){struct transfer').replace('m.port.disposition=MACH_MSG_TYPE_COPY_SEND;m.port.type','m.port.disposition=move?MACH_MSG_TYPE_MOVE_SEND:MACH_MSG_TYPE_COPY_SEND;m.port.type',1)
t=t.replace('static int run_case(int mode,const char *folder,const char *exe)', 'static int run_case(int mode,int initial_move,const char *folder,const char *exe)')
t=t.replace('int waited=0,registered=0,result=73;', 'int waited=0,registered=0,result=73,initial_query=0,error_query=0;unsigned error_refs=0;mach_port_t initial_name=0;')
a='remote=ready.ack.h.msgh_remote_port;if(!remote||transfer(remote,resource,91,sid))goto done;'
b='remote=ready.ack.h.msgh_remote_port;initial_name=resource;if(!remote||transfer(remote,resource,91,sid,initial_move))goto done;mach_port_type_t initial_type=0;initial_query=mach_port_type(mach_task_self(),initial_name,&initial_type);if(initial_move){if(initial_query!=15)goto done;resource=0;}else if(initial_query||refs(resource)!=1)goto done;'
if a not in t:raise ValueError('Initial send needle')
t=t.replace(a,b)
a='if(receive_message(&ack,inbox)||!confirm(&ack,child,1)||refs(resource)!=1||!snapshot_checked(surface,folder,"sender-after-error.bin",0))goto done;'
b='if(receive_message(&ack,inbox)||!confirm(&ack,child,1))goto done;error_query=mach_port_type(mach_task_self(),initial_name,&initial_type);if(initial_move){if(error_query!=15)goto done;error_refs=0;}else {if(error_query||refs(resource)!=1)goto done;error_refs=refs(resource);}if(!snapshot_checked(surface,folder,"sender-after-error.bin",0))goto done;'
if a not in t:raise ValueError('Stage needle')
t=t.replace(a,b)
a='if(!mutate(surface,0,0x5a)||!snapshot_checked(surface,folder,"sender-mutated.bin",1)||transfer(remote,resource,92,sid)||refs(resource)!=1)goto done;'
b='if(!mutate(surface,0,0x5a)||!snapshot_checked(surface,folder,"sender-mutated.bin",1))goto done;if(initial_move){resource=IOSurfaceCreateMachPort(surface);if(!resource||refs(resource)!=1)goto done;}if(transfer(remote,resource,92,sid,0)||refs(resource)!=1)goto done;'
if a not in t:raise ValueError('Retry needle')
t=t.replace(a,b)
t=t.replace('\\"sender_refs_after_error\\":1,','\\"sender_refs_after_error\\":%u,\\"initial_move\\":%s,\\"initial_query\\":%d,\\"initial_query_after_error\\":%d,\\"initial_disposition\\":%d,\\"reacquired_resource\\":%s,')
t=t.replace('getpid(),child,mode,sid,query)<0','getpid(),child,mode,sid,error_refs,initial_move?"true":"false",initial_query,error_query,initial_move?MACH_MSG_TYPE_MOVE_SEND:MACH_MSG_TYPE_COPY_SEND,initial_move?"true":"false",query)<0')
a='for(int i=0;i<3;i++){char path[1024];if(snprintf(path,sizeof(path),"%s/%s",argv[2],i==0?"control":i==1?"large":"small")>=(int)sizeof(path))return 2;int code=run_case(i,path,argv[0]);'
b='for(int i=0;i<6;i++){int mode=i%3,move=i/3;char path[1024];if(snprintf(path,sizeof(path),"%s/%s-%s",argv[2],move?"move":"copy",mode==0?"control":mode==1?"large":"small")>=(int)sizeof(path))return 2;int code=run_case(mode,move,path,argv[0]);'
if a not in t:raise ValueError('Main needle')
t=t.replace(a,b);(d/'probe.c').write_text(t)
for kind in ['copy','move']:
 for mode in ['control','large','small']:(d/'owned-documents'/(kind+'-'+mode)).mkdir(parents=True)
print(hashlib.sha256(t.encode()).hexdigest())
