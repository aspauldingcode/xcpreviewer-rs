#include "reuse_primitives.c"
static int gone(mach_port_t p){mach_port_type_t t=0;return mach_port_type(mach_task_self(),p,&t)==KERN_INVALID_NAME;}
static int capture(IOSurfaceRef s,const char *folder,const char *name){uint8_t raw[LIMIT];size_t n=IOSurfaceGetAllocSize(s);return n && n<=LIMIT && snapshot(s,raw,n) && write_bytes(folder,name,raw,n);}
static int ack_at(mach_port_t inbox,pid_t peer,unsigned stage){union receive m;return !receive_message(&m,inbox) && peer_matches(&m,peer) && m.ack.h.msgh_size==sizeof(struct ack) && m.ack.magic==MAGIC && m.ack.stage==stage && m.ack.value==1;}
static int alias_peer(const char *service,pid_t parent,const char *folder){
 mach_port_t remote=MACH_PORT_NULL,inbox=MACH_PORT_NULL,resource=MACH_PORT_NULL;IOSurfaceRef alias=NULL;int result=4;
 if(bootstrap_look_up(bootstrap_port,service,&remote) || mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox))goto done;
 struct ack ready={0};ready.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,MACH_MSG_TYPE_MAKE_SEND);ready.h.msgh_size=sizeof(ready);ready.h.msgh_remote_port=remote;ready.h.msgh_local_port=inbox;ready.magic=MAGIC;
 if(mach_msg(&ready.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(ready),0,MACH_PORT_NULL,3000,MACH_PORT_NULL) || !receive_surface(inbox,parent,1,&alias,&resource) || !send_refs(resource,1))goto done;
 if(IOSurfaceGetWidth(alias)!=17 || IOSurfaceGetHeight(alias)!=9 || IOSurfaceGetBytesPerRow(alias)!=128 || IOSurfaceGetAllocSize(alias)!=16384)goto done;
 mach_port_t old=resource;if(mach_port_deallocate(mach_task_self(),resource) || !gone(old))goto done;resource=MACH_PORT_NULL;
 if(!capture(alias,folder,"peer-before.bin"))goto done;
 char path[4096];snprintf(path,sizeof(path),"%s/peer.json",folder);FILE *file=fopen(path,"w");if(!file)goto done;
 fprintf(file,"{\"pid\":%d,\"parent\":%d,\"surface_id\":%u,\"audit_peer_verified\":true,\"imported_right_released\":true,\"local_resource_name_removed\":true,\"cf_alias_retained\":true}\n",getpid(),parent,IOSurfaceGetID(alias));if(fclose(file))goto done;
 if(send_ack(remote,1,1) || !ack_at(inbox,parent,6) || !capture(alias,folder,"peer-after-churn.bin") || send_ack(remote,5,1) || !ack_at(inbox,parent,7))goto done;
 CFRelease(alias);alias=NULL;if(send_ack(remote,3,1))goto done;result=0;
 done:if(alias)CFRelease(alias);if(MACH_PORT_VALID(resource))mach_port_deallocate(mach_task_self(),resource);if(MACH_PORT_VALID(inbox))mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);if(MACH_PORT_VALID(remote))mach_port_deallocate(mach_task_self(),remote);return result;
}
static int one(const char *binary,const char *mode,const char *folder){
 IOSurfaceRef original=NULL,candidate=NULL,lookup=NULL;mach_port_t inbox=MACH_PORT_NULL,remote=MACH_PORT_NULL,resource=MACH_PORT_NULL;pid_t child=-1;int registered=0,waited=0,status=0,result=3,global_present=0,matched=0;uint32_t oldid=0,heldids[64]={0},afterids[64]={0};unsigned attempts=0;char service[128],pidtext[32],hex[33];unsigned char nonce[16];arc4random_buf(nonce,sizeof(nonce));for(unsigned i=0;i<16;i++)sprintf(hex+i*2,"%02x",nonce[i]);snprintf(service,sizeof(service),"local.re.surface.%d.%s",getpid(),hex);snprintf(pidtext,sizeof(pidtext),"%d",getpid());
 if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox) || mach_port_insert_right(mach_task_self(),inbox,inbox,MACH_MSG_TYPE_MAKE_SEND) || bootstrap_register(bootstrap_port,service,inbox))goto done;registered=1;
 original=create_surface(17,9,49,NULL);if(!original || !capture(original,folder,"initial.bin"))goto done;oldid=IOSurfaceGetID(original);resource=IOSurfaceCreateMachPort(original);if(!MACH_PORT_VALID(resource) || !send_refs(resource,1))goto done;
 child=fork();if(child==0){execl(binary,binary,"--alias-peer",service,pidtext,folder,NULL);_exit(127);}if(child<0)goto done;
 union receive ready;if(receive_message(&ready,inbox) || !peer_matches(&ready,child) || ready.ack.magic!=MAGIC || ready.ack.stage!=0)goto done;remote=ready.ack.h.msgh_remote_port;
 if(!transfer_surface(remote,resource,original,49,1) || !ack_at(inbox,child,1))goto done;
 CFRelease(original);original=NULL;mach_port_t old=resource;if(mach_port_deallocate(mach_task_self(),resource) || !gone(old))goto done;resource=MACH_PORT_NULL;
 for(unsigned i=0;i<64;i++){
  candidate=create_surface(17,9,50,NULL);if(!candidate)goto done;heldids[i]=IOSurfaceGetID(candidate);if(heldids[i]==oldid)goto done;char name[64];snprintf(name,sizeof(name),"held-candidate-%03u.bin",i);if(!capture(candidate,folder,name))goto done;CFRelease(candidate);candidate=NULL;
 }
 lookup=IOSurfaceLookup(oldid);global_present=lookup!=NULL;if(lookup){if(!capture(lookup,folder,"global-while-peer.bin"))goto done;CFRelease(lookup);lookup=NULL;}
 if(send_ack(remote,6,1) || !ack_at(inbox,child,5))goto done;
 if(!strcmp(mode,"abrupt")){if(kill(child,SIGKILL))goto done;}else{if(send_ack(remote,7,1) || !ack_at(inbox,child,3))goto done;}
 if(waitpid(child,&status,0)!=child)goto done;waited=1;if(!strcmp(mode,"abrupt")?(!WIFSIGNALED(status)||WTERMSIG(status)!=SIGKILL):(!WIFEXITED(status)||WEXITSTATUS(status)!=0))goto done;
 usleep(100000);lookup=IOSurfaceLookup(oldid);int before_present=lookup!=NULL;if(lookup){if(!capture(lookup,folder,"lookup-after-peer.bin"))goto done;CFRelease(lookup);lookup=NULL;}
 for(unsigned i=0;i<64;i++){
  candidate=create_surface(17,9,50,NULL);if(!candidate)goto done;afterids[attempts++]=IOSurfaceGetID(candidate);char name[64];snprintf(name,sizeof(name),"after-candidate-%03u.bin",i);if(!capture(candidate,folder,name))goto done;
  if(afterids[i]==oldid){matched=1;lookup=IOSurfaceLookup(oldid);if(!lookup || !capture(lookup,folder,"stale-lookup.bin"))goto done;CFRelease(lookup);lookup=NULL;break;}
  CFRelease(candidate);candidate=NULL;
 }
 if(candidate){CFRelease(candidate);candidate=NULL;}if(!remove_rendezvous(&inbox,service))goto done;registered=0;old=remote;if(mach_port_deallocate(mach_task_self(),remote) || !gone(old))goto done;remote=MACH_PORT_NULL;
 printf("{\"mode\":\"%s\",\"sender_pid\":%d,\"receiver_pid\":%d,\"old_id\":%u,\"allocation_bytes\":16384,\"stride\":128,\"parent_cf_owner_released\":true,\"parent_surface_right_removed\":true,\"held_creations\":64,\"global_lookup_while_peer\":%s,\"peer_exit\":%d,\"peer_signal\":%d,\"lookup_after_peer\":%s,\"attempts_after_peer\":%u,\"matched_after_peer\":%s,\"rendezvous_removed\":true,\"peer_endpoint_name_removed\":true,\"held_ids\":[",mode,getpid(),child,oldid,global_present?"true":"false",WIFEXITED(status)?WEXITSTATUS(status):-1,WIFSIGNALED(status)?WTERMSIG(status):0,before_present?"true":"false",attempts,matched?"true":"false");
 for(unsigned i=0;i<64;i++)printf("%s%u",i?",":"",heldids[i]);printf("],\"after_ids\":[");for(unsigned i=0;i<attempts;i++)printf("%s%u",i?",":"",afterids[i]);printf("]}\n");result=0;
 done:if(child>0&&!waited){kill(child,SIGKILL);waitpid(child,NULL,0);}if(lookup)CFRelease(lookup);if(candidate)CFRelease(candidate);if(original)CFRelease(original);if(MACH_PORT_VALID(resource))mach_port_deallocate(mach_task_self(),resource);if(registered)remove_rendezvous(&inbox,service);if(MACH_PORT_VALID(remote))mach_port_deallocate(mach_task_self(),remote);if(MACH_PORT_VALID(inbox))mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);return result;
}
int main(int argc,char **argv){
 alarm(12);if(argc==5 && !strcmp(argv[1],"--alias-peer")){char *end=NULL;long parent=strtol(argv[3],&end,10);if(!end||*end||parent<=1||getppid()!=parent)return 2;return alias_peer(argv[2],(pid_t)parent,argv[4]);}
 if(argc!=2)return 2;const char *modes[]={"clean","abrupt"};for(unsigned i=0;i<2;i++){char folder[4096];snprintf(folder,sizeof(folder),"%s/%s",argv[1],modes[i]);int result=one(argv[0],modes[i],folder);if(result)return result;}return 0;
}
