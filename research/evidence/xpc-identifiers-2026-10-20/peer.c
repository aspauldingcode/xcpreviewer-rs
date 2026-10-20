#include "peer.h"
#include <servers/bootstrap.h>
#include <bsm/libbsm.h>
#include <sys/wait.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>
#include <time.h>
static mach_port_t inbox,remote;static pid_t child;static char service[128];static int role,reaped;
struct transfer {mach_msg_header_t h;mach_msg_body_t b;mach_msg_port_descriptor_t p;};
union recv {struct transfer m;unsigned char bytes[sizeof(struct transfer)+MAX_TRAILER_SIZE+32];};
static void receive(union recv*r,pid_t pid){memset(r,0,sizeof(*r));if(mach_msg(&r->m.h,MACH_RCV_MSG|MACH_RCV_TIMEOUT|MACH_RCV_TRAILER_TYPE(0)|MACH_RCV_TRAILER_ELEMENTS(MACH_RCV_TRAILER_AUDIT),0,sizeof(*r),inbox,2000,0))exit(50);size_t off=(r->m.h.msgh_size+3u)&~3u;if(off+sizeof(mach_msg_audit_trailer_t)>sizeof(*r))exit(51);mach_msg_audit_trailer_t*t=(void*)(r->bytes+off);if(t->msgh_trailer_type||t->msgh_trailer_size<sizeof(*t)||audit_token_to_pid(t->msgh_audit)!=pid)exit(52);}
int peer_setup(int argc,char**argv){if(argc!=3&&argc!=5)exit(40);role=argc==5;if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox))exit(41);
 if(role){if(bootstrap_look_up(bootstrap_port,argv[3],&remote))exit(42);mach_msg_header_t ready={0};ready.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,MACH_MSG_TYPE_MAKE_SEND);ready.msgh_size=sizeof(ready);ready.msgh_remote_port=remote;ready.msgh_local_port=inbox;ready.msgh_id=73;if(mach_msg(&ready,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(ready),0,0,500,0))exit(43);union recv r;receive(&r,(pid_t)atoi(argv[4]));if(r.m.h.msgh_size!=sizeof(struct transfer)||!(r.m.h.msgh_bits&MACH_MSGH_BITS_COMPLEX)||r.m.b.msgh_descriptor_count!=1||r.m.p.type!=MACH_MSG_PORT_DESCRIPTOR||r.m.p.disposition!=MACH_MSG_TYPE_PORT_SEND_ONCE)exit(44);trace_route(r.m.p.name,0);char path[4096];snprintf(path,sizeof(path),"%s/child.json",argv[2]);if(!freopen(path,"w",stdout))exit(45);return 1;}
 if(mach_port_insert_right(mach_task_self(),inbox,inbox,MACH_MSG_TYPE_MAKE_SEND))exit(46);snprintf(service,sizeof(service),"local.re.xpcpeer.%d.%08x",getpid(),arc4random());if(bootstrap_register(bootstrap_port,service,inbox))exit(47);char pid[32];snprintf(pid,sizeof(pid),"%d",getpid());child=fork();if(!child){execl(argv[0],argv[0],argv[1],argv[2],service,pid,NULL);_exit(127);}if(child<0)exit(48);union recv r;receive(&r,child);if(r.m.h.msgh_size!=sizeof(mach_msg_header_t)||r.m.h.msgh_id!=73)exit(49);remote=r.m.h.msgh_remote_port;trace_route(remote,1);return 0;
}
void peer_wait_for_exit(void){if(!role&&!reaped){int status=0,done=0;for(int i=0;i<200;i++){pid_t p=waitpid(child,&status,WNOHANG);if(p==child){done=1;break;}struct timespec t={0,10000000};nanosleep(&t,0);}if(!done){kill(child,SIGKILL);waitpid(child,0,0);exit(53);}if(!WIFEXITED(status)||WEXITSTATUS(status))exit(54);reaped=1;}}
void peer_finish(void){peer_wait_for_exit();if(remote)mach_port_deallocate(mach_task_self(),remote);mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);if(!role){mach_port_deallocate(mach_task_self(),inbox);int gone=0;for(int i=0;i<100;i++){mach_port_t found=0;if(bootstrap_look_up(bootstrap_port,service,&found)==BOOTSTRAP_UNKNOWN_SERVICE){gone=1;break;}if(found)mach_port_deallocate(mach_task_self(),found);struct timespec t={0,10000000};nanosleep(&t,0);}if(!gone)exit(55);}}
int peer_is_reaped(void){return reaped;}
