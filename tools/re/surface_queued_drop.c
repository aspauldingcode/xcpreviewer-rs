// Discard an owned queued descriptor without receiving/importing it.
#define main reused_surface_main
#include "surface_ipc_probe.c"
#undef main
static int gone(mach_port_t p){mach_port_type_t t=0;return mach_port_type(mach_task_self(),p,&t)==KERN_INVALID_NAME;}
static int peer(const char*service,pid_t parent){
 mach_port_t remote=0,inbox=0,control=0;int result=50;
 if(bootstrap_look_up(bootstrap_port,service,&remote)||mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox)||mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&control))goto done;
 struct transfer ready={0};ready.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,MACH_MSG_TYPE_MAKE_SEND)|MACH_MSGH_BITS_COMPLEX;ready.h.msgh_size=sizeof(ready);ready.h.msgh_remote_port=remote;ready.h.msgh_local_port=inbox;
 ready.body.msgh_descriptor_count=1;ready.port.name=control;ready.port.disposition=MACH_MSG_TYPE_MAKE_SEND;ready.port.type=MACH_MSG_PORT_DESCRIPTOR;ready.magic=MAGIC;
 if(mach_msg(&ready.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(ready),0,MACH_PORT_NULL,3000,MACH_PORT_NULL))goto done;
 union receive go;if(receive_message(&go,control)||!peer_matches(&go,parent)||go.ack.h.msgh_size!=sizeof(struct ack)||go.ack.magic!=MAGIC||go.ack.stage!=6)goto done;
 mach_port_status_t status={0};mach_msg_type_number_t count=MACH_PORT_RECEIVE_STATUS_COUNT;
 if(mach_port_get_attributes(mach_task_self(),inbox,MACH_PORT_RECEIVE_STATUS,(mach_port_info_t)&status,&count)||status.mps_msgcount!=1)goto done;
 mach_port_t old=inbox;if(mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1)||!gone(old))goto done;inbox=0;
 old=control;if(mach_port_mod_refs(mach_task_self(),control,MACH_PORT_RIGHT_RECEIVE,-1)||!gone(old))goto done;control=0;
 if(send_ack(remote,7,status.mps_msgcount))goto done;
 old=remote;if(mach_port_deallocate(mach_task_self(),remote)||!gone(old))goto done;remote=0;result=45;
 done:if(inbox)mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);if(control)mach_port_mod_refs(mach_task_self(),control,MACH_PORT_RIGHT_RECEIVE,-1);if(remote)mach_port_deallocate(mach_task_self(),remote);return result;
}
int main(int argc,char**argv){
 alarm(12);if(argc==4&&!strcmp(argv[1],"--peer")){char*end;long p=strtol(argv[3],&end,10);if(*end||p<=1||getppid()!=p)return 2;return peer(argv[2],(pid_t)p);}
 if(argc!=3||(strcmp(argv[1],"copy")&&strcmp(argv[1],"move")))return 2;
 int move=!strcmp(argv[1],"move"),result=51,registered=0,waited=0,waitStatus=0;pid_t child=-1;
 mach_port_t inbox=0,remote=0,control=0,resource=0,replacement=0;IOSurfaceRef surface=NULL,alias=NULL;
 unsigned char nonce[16];char hex[33],service[128],parentPID[32];arc4random_buf(nonce,16);for(int i=0;i<16;i++)sprintf(hex+i*2,"%02x",nonce[i]);snprintf(service,sizeof(service),"local.re.queued.%d.%s",getpid(),hex);snprintf(parentPID,sizeof(parentPID),"%d",getpid());
 uint8_t raw[LIMIT],expected[LIMIT];size_t stride=0,allocation=0;uint32_t sid=0;
 if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox)||mach_port_insert_right(mach_task_self(),inbox,inbox,MACH_MSG_TYPE_MAKE_SEND)||bootstrap_register(bootstrap_port,service,inbox))goto done;registered=1;
 surface=create_surface(11,6,33,NULL);if(!surface)goto done;stride=IOSurfaceGetBytesPerRow(surface);allocation=IOSurfaceGetAllocSize(surface);sid=IOSurfaceGetID(surface);if(allocation>LIMIT)goto done;
 pattern(expected,stride,11,6,33,allocation);if(!snapshot(surface,raw,allocation)||memcmp(raw,expected,allocation)||!write_bytes(argv[2],"before.bin",raw,allocation))goto done;
 resource=IOSurfaceCreateMachPort(surface);if(!send_refs(resource,1))goto done;
 child=fork();if(child==0){execl(argv[0],argv[0],"--peer",service,parentPID,NULL);_exit(127);}if(child<0)goto done;
 union receive ready;if(receive_message(&ready,inbox)||!peer_matches(&ready,child)||ready.transfer.h.msgh_size!=sizeof(struct transfer)||!(ready.transfer.h.msgh_bits&MACH_MSGH_BITS_COMPLEX)||ready.transfer.body.msgh_descriptor_count!=1||ready.transfer.port.type!=MACH_MSG_PORT_DESCRIPTOR||ready.transfer.port.disposition!=MACH_MSG_TYPE_PORT_SEND||ready.transfer.magic!=MAGIC){mach_msg_destroy(&ready.transfer.h);goto done;}
 remote=ready.transfer.h.msgh_remote_port;control=ready.transfer.port.name;if(!MACH_PORT_VALID(remote)||!MACH_PORT_VALID(control))goto done;
 struct transfer m={0};m.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0)|MACH_MSGH_BITS_COMPLEX;m.h.msgh_size=sizeof(m);m.h.msgh_remote_port=remote;m.body.msgh_descriptor_count=1;m.port.name=resource;m.port.disposition=move?MACH_MSG_TYPE_MOVE_SEND:MACH_MSG_TYPE_COPY_SEND;m.port.type=MACH_MSG_PORT_DESCRIPTOR;m.magic=MAGIC;m.width=11;m.height=6;m.seed=33;m.stride=(uint32_t)stride;m.surface_id=sid;
 if(mach_msg(&m.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(m),0,MACH_PORT_NULL,3000,MACH_PORT_NULL))goto done;
 int refsAfterSend=move?0:1;if(move){if(!gone(resource))goto done;resource=0;}else if(!send_refs(resource,1))goto done;
 if(send_ack(control,6,1))goto done;
 union receive dropped;if(receive_message(&dropped,inbox)||!peer_matches(&dropped,child)||dropped.ack.h.msgh_size!=sizeof(struct ack)||dropped.ack.magic!=MAGIC||dropped.ack.stage!=7||dropped.ack.value!=1)goto done;
 if(waitpid(child,&waitStatus,0)!=child)goto done;waited=1;if(!WIFEXITED(waitStatus)||WEXITSTATUS(waitStatus)!=45)goto done;
 mach_port_type_t rt=0,ct=0;if(mach_port_type(mach_task_self(),remote,&rt)||!(rt&MACH_PORT_TYPE_DEAD_NAME)||mach_port_type(mach_task_self(),control,&ct)||!(ct&MACH_PORT_TYPE_DEAD_NAME))goto done;
 if(!snapshot(surface,raw,allocation)||memcmp(raw,expected,allocation)||!write_bytes(argv[2],"after-drop.bin",raw,allocation)||!mutate(surface,0,0x5a))goto done;expected[0]^=0x5a;
 if(resource){mach_port_t old=resource;if(mach_port_deallocate(mach_task_self(),resource)||!gone(old))goto done;resource=0;}
 replacement=IOSurfaceCreateMachPort(surface);if(!send_refs(replacement,1))goto done;CFRelease(surface);surface=NULL;alias=IOSurfaceLookupFromMachPort(replacement);
 if(!alias||IOSurfaceGetID(alias)!=sid||!snapshot(alias,raw,allocation)||memcmp(raw,expected,allocation)||!write_bytes(argv[2],"port-only.bin",raw,allocation))goto done;CFRelease(alias);alias=NULL;
 mach_port_t old=replacement;if(mach_port_deallocate(mach_task_self(),replacement)||!gone(old))goto done;replacement=0;
 old=remote;if(mach_port_deallocate(mach_task_self(),remote)||!gone(old))goto done;remote=0;old=control;if(mach_port_deallocate(mach_task_self(),control)||!gone(old))goto done;control=0;
 if(!remove_rendezvous(&inbox,service))goto done;registered=0;
 printf("{\"mode\":\"%s\",\"sender_pid\":%d,\"receiver_pid\":%d,\"peer_exit\":45,\"peer_signal\":0,\"width\":11,\"height\":6,\"seed\":33,\"stride\":%zu,\"allocation_bytes\":%zu,\"queued_messages_before_drop\":1,\"sender_refs_after_send\":%d,\"replacement_refs\":1,\"final_names_removed\":true,\"peer_endpoints_dead\":true,\"audit_peers_verified\":true,\"receiver_imported\":false,\"completion_accepted\":false,\"rendezvous_removed\":true}\n",argv[1],getpid(),child,stride,allocation,refsAfterSend);result=0;
 done:if(child>0&&!waited){kill(child,SIGKILL);waitpid(child,NULL,0);}if(alias)CFRelease(alias);if(surface)CFRelease(surface);if(resource)mach_port_deallocate(mach_task_self(),resource);if(replacement)mach_port_deallocate(mach_task_self(),replacement);if(remote)mach_port_deallocate(mach_task_self(),remote);if(control)mach_port_deallocate(mach_task_self(),control);if(registered)remove_rendezvous(&inbox,service);else if(inbox)mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);return result;
}
