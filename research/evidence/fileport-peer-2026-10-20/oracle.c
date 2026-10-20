// Original owned-peer control. Uses SDK-declared Mach, fileport and Unix APIs only.
#include <mach/mach.h>
#include <servers/bootstrap.h>
#include <bsm/libbsm.h>
#include <sys/fileport.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <errno.h>
struct packet { mach_msg_header_t h; mach_msg_body_t body; mach_msg_port_descriptor_t fd; unsigned char payload[32]; };
union incoming { struct packet p; unsigned char bytes[sizeof(struct packet)+MAX_TRAILER_SIZE+32]; };
static const unsigned char content[]="owned-cross-process-capability";
static void save(const char *dir,const char *name,const void *p,size_t n){char path[4096];snprintf(path,sizeof(path),"%s/%s",dir,name);FILE *f=fopen(path,"wb");if(!f||fwrite(p,1,n,f)!=n||fclose(f))exit(70);}
static int no_refs(mach_port_t p){mach_port_urefs_t n=999;int r=mach_port_get_refs(mach_task_self(),p,MACH_PORT_RIGHT_SEND,&n);return r==KERN_INVALID_NAME||r==KERN_INVALID_RIGHT||(r==0&&n==0);}
static int child(const char *service,const char *mode,const char *dir){
 mach_port_t remote=0,port=0;if(bootstrap_look_up(bootstrap_port,service,&remote))return 10;
 if(!strcmp(mode,"no-send")){mach_port_deallocate(mach_task_self(),remote);return 24;}
 int fds[2];if(pipe(fds)||fcntl(fds[0],F_SETFL,O_NONBLOCK))return 11;
 if(write(fds[1],content,sizeof(content))!=sizeof(content)||close(fds[1]))return 12;
 if(fileport_makeport(fds[0],&port)||close(fds[0]))return 13;
 struct packet p={0};p.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0)|MACH_MSGH_BITS_COMPLEX;p.h.msgh_size=sizeof(p);p.h.msgh_remote_port=remote;p.h.msgh_id=0x46504431;
 p.body.msgh_descriptor_count=1;p.fd.name=port;p.fd.disposition=MACH_MSG_TYPE_COPY_SEND;p.fd.type=MACH_MSG_PORT_DESCRIPTOR;
 for(size_t i=0;i<sizeof(p.payload);i++)p.payload[i]=(unsigned char)(17+i*37);
 save(dir,"send.bin",(char*)&p+sizeof(p.h),sizeof(p)-sizeof(p.h));
 int r=mach_msg(&p.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(p),0,0,500,0);if(r)return 14;
 if(!strcmp(mode,"abrupt"))_exit(23); // Deliberately leave both owned send refs for process teardown.
 if(mach_port_deallocate(mach_task_self(),port)||!no_refs(port)||mach_port_deallocate(mach_task_self(),remote))return 15;
 return 0;
}
int main(int argc,char **argv){
 if(argc==5&&!strcmp(argv[1],"--child"))return child(argv[2],argv[3],argv[4]);
 if(argc!=3)return 2;const char *mode=argv[1],*dir=argv[2];if(strcmp(mode,"clean")&&strcmp(mode,"abrupt")&&strcmp(mode,"no-send"))return 2;
 mach_port_t inbox=0,port=0;pid_t pid=-1;int reaped=0,registered=0,fdA=-1,fdB=-1,result=30;char name[128];snprintf(name,sizeof(name),"local.re.fileport.%d.%08x",getpid(),arc4random());
 if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox)||mach_port_insert_right(mach_task_self(),inbox,inbox,MACH_MSG_TYPE_MAKE_SEND)||bootstrap_register(bootstrap_port,name,inbox))goto done;registered=1;
 pid=fork();if(pid==0){execl(argv[0],argv[0],"--child",name,mode,dir,NULL);_exit(127);}if(pid<0)goto done;
 union incoming m={0};int r=mach_msg(&m.p.h,MACH_RCV_MSG|MACH_RCV_TIMEOUT|MACH_RCV_TRAILER_TYPE(MACH_MSG_TRAILER_FORMAT_0)|MACH_RCV_TRAILER_ELEMENTS(MACH_RCV_TRAILER_AUDIT),0,sizeof(m),inbox,500,0);
 int status=0;for(int i=0;i<100;i++){pid_t w=waitpid(pid,&status,WNOHANG);if(w==pid){reaped=1;break;}if(w<0)goto done;struct timespec t={0,10000000};nanosleep(&t,0);}if(!reaped||!WIFEXITED(status))goto done;
 if(!strcmp(mode,"no-send")){if(r!=MACH_RCV_TIMED_OUT||WEXITSTATUS(status)!=24)goto done;result=0;goto drain;}
 if(r||WEXITSTATUS(status)!=(!strcmp(mode,"abrupt")?23:0))goto done;
 size_t off=(m.p.h.msgh_size+3u)&~3u;if(off+sizeof(mach_msg_audit_trailer_t)>sizeof(m))goto done;
 mach_msg_audit_trailer_t *t=(void*)(m.bytes+off);
 if(t->msgh_trailer_type!=0||t->msgh_trailer_size<sizeof(*t)||audit_token_to_pid(t->msgh_audit)!=pid)goto done;
 if(m.p.h.msgh_size!=sizeof(struct packet)||!(m.p.h.msgh_bits&MACH_MSGH_BITS_COMPLEX)||m.p.body.msgh_descriptor_count!=1||m.p.fd.type!=MACH_MSG_PORT_DESCRIPTOR||m.p.fd.disposition!=MACH_MSG_TYPE_PORT_SEND)goto done;
 port=m.p.fd.name;save(dir,"receive.bin",(char*)&m.p+sizeof(m.p.h),sizeof(m.p)-sizeof(m.p.h));
 mach_port_urefs_t refs=0;if(mach_port_get_refs(mach_task_self(),port,MACH_PORT_RIGHT_SEND,&refs)||refs!=1)goto done;
 fdA=fileport_makefd(port);fdB=fileport_makefd(port);if(fdA<0||fdB<0)goto done;
 unsigned char got[sizeof(content)]={0};size_t half=sizeof(content)/2;if(read(fdA,got,half)!=(ssize_t)half)goto done;
 mach_port_t old=port;if(mach_port_deallocate(mach_task_self(),port)||!no_refs(old))goto done;port=0;
 if(read(fdB,got+half,sizeof(got)-half)!=(ssize_t)(sizeof(got)-half)||memcmp(got,content,sizeof(got)))goto done;
 unsigned char extra;if(read(fdA,&extra,1)!=0||read(fdB,&extra,1)!=0)goto done;
 save(dir,"content.bin",got,sizeof(got));int oldA=fdA,oldB=fdB;if(close(fdA)||close(fdB))goto done;fdA=fdB=-1;errno=0;if(fcntl(oldA,F_GETFD)!=-1||errno!=EBADF)goto done;errno=0;if(fcntl(oldB,F_GETFD)!=-1||errno!=EBADF)goto done;result=0;
 drain:
 memset(&m,0,sizeof(m));if(mach_msg(&m.p.h,MACH_RCV_MSG|MACH_RCV_TIMEOUT,0,sizeof(m),inbox,0,0)!=MACH_RCV_TIMED_OUT)result=32;
 done:
 if(pid>0&&!reaped){kill(pid,SIGKILL);waitpid(pid,0,0);}
 if(fdA>=0)close(fdA);if(fdB>=0)close(fdB);if(port)mach_port_deallocate(mach_task_self(),port);
 int removed=0;if(inbox){mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);mach_port_deallocate(mach_task_self(),inbox);}
 if(registered)for(int i=0;i<100;i++){mach_port_t found=0;int code=bootstrap_look_up(bootstrap_port,name,&found);if(code==BOOTSTRAP_UNKNOWN_SERVICE){removed=1;break;}if(found)mach_port_deallocate(mach_task_self(),found);struct timespec t={0,10000000};nanosleep(&t,0);}
 if(!removed)result=31;
 printf("{\"mode\":\"%s\",\"ok\":%s,\"peer_reaped\":%s,\"rendezvous_removed\":%s,\"resource_read_after_peer_exit\":%s,\"port_released_before_second_read\":%s,\"post_reap_queue_empty\":%s,\"final_kernel_reclamation_proven\":false}\n",mode,result?"false":"true",reaped?"true":"false",removed?"true":"false",!result&&strcmp(mode,"no-send")?"true":"false",!result&&strcmp(mode,"no-send")?"true":"false",!result?"true":"false");return result;
}
