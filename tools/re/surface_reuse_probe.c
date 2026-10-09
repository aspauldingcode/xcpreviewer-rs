#define main surface_success_main
#include "surface_ipc_probe.c"
#undef main

static int receive_surface(mach_port_t inbox,pid_t peer,unsigned stage,IOSurfaceRef *surface,mach_port_t *port) {
    union receive message;if(receive_message(&message,inbox))return 0;struct transfer *m=&message.transfer;
    if(!peer_matches(&message,peer) || m->h.msgh_size!=sizeof(*m) || !(m->h.msgh_bits&MACH_MSGH_BITS_COMPLEX) || m->body.msgh_descriptor_count!=1 || m->port.type!=MACH_MSG_PORT_DESCRIPTOR || m->port.disposition!=MACH_MSG_TYPE_PORT_SEND || m->magic!=MAGIC || m->h.msgh_id!=(int)(200+stage)){mach_msg_destroy(&m->h);return 0;}
    *port=m->port.name;*surface=IOSurfaceLookupFromMachPort(*port);
    return *surface && IOSurfaceGetID(*surface)==m->surface_id;
}
static int transfer_surface(mach_port_t endpoint,mach_port_t resource,IOSurfaceRef surface,unsigned seed,unsigned stage) {
    struct transfer m={0};m.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0)|MACH_MSGH_BITS_COMPLEX;m.h.msgh_size=sizeof(m);m.h.msgh_remote_port=endpoint;m.h.msgh_id=200+stage;
    m.body.msgh_descriptor_count=1;m.port.name=resource;m.port.disposition=MACH_MSG_TYPE_COPY_SEND;m.port.type=MACH_MSG_PORT_DESCRIPTOR;
    m.magic=MAGIC;m.width=(uint32_t)IOSurfaceGetWidth(surface);m.height=(uint32_t)IOSurfaceGetHeight(surface);m.seed=seed;m.stride=(uint32_t)IOSurfaceGetBytesPerRow(surface);m.surface_id=IOSurfaceGetID(surface);
    return mach_msg(&m.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(m),0,MACH_PORT_NULL,3000,MACH_PORT_NULL)==KERN_SUCCESS;
}
// A task-local name and a retained CF alias have independent lifetimes.
static uint32_t lookup_id(mach_port_t name) {
    IOSurfaceRef surface=IOSurfaceLookupFromMachPort(name);
    if(!surface)return 0;
    uint32_t id=IOSurfaceGetID(surface);CFRelease(surface);return id;
}
// ID lookup is a separate observable from task-local Mach-name lookup.
static uint32_t global_lookup_id(uint32_t id) {
    IOSurfaceRef surface=IOSurfaceLookup(id);
    if(!surface)return 0;
    uint32_t found=IOSurfaceGetID(surface);CFRelease(surface);return found;
}
static int reuse_peer(const char *service,pid_t parent,const char *mode,const char *folder) {
    mach_port_t remote=MACH_PORT_NULL,inbox=MACH_PORT_NULL,p1=MACH_PORT_NULL,p2=MACH_PORT_NULL;
    IOSurfaceRef first=NULL,second=NULL;int same=!strcmp(mode,"reuse"),result=50;uint8_t raw[LIMIT];
    if(bootstrap_look_up(bootstrap_port,service,&remote) || mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox))goto done;
    struct ack ready={0};ready.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,MACH_MSG_TYPE_MAKE_SEND);ready.h.msgh_size=sizeof(ready);ready.h.msgh_remote_port=remote;ready.h.msgh_local_port=inbox;ready.magic=MAGIC;
    if(mach_msg(&ready.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(ready),0,MACH_PORT_NULL,3000,MACH_PORT_NULL))goto done;
    if(!receive_surface(inbox,parent,1,&first,&p1) || !send_refs(p1,1) || send_ack(remote,1,1))goto done;
    if(!receive_surface(inbox,parent,2,&second,&p2))goto done;
    uint32_t id1=IOSurfaceGetID(first),id2=IOSurfaceGetID(second);
    if((id1==id2)!=same || (p1==p2)!=same || !send_refs(p1,same?2:1) || !send_refs(p2,same?2:1))goto done;
    size_t width=IOSurfaceGetWidth(first),height=IOSurfaceGetHeight(first),stride=IOSurfaceGetBytesPerRow(first),count=stride*height;
    if(!width || width>64 || !height || height>16 || stride<width*4 || count>LIMIT || IOSurfaceGetWidth(second)!=width || IOSurfaceGetHeight(second)!=height || IOSurfaceGetBytesPerRow(second)!=stride)goto done;
    // No read of the first handle occurs until the producer has supplied generation two.
    if(!snapshot(first,raw,count) || !write_bytes(folder,"delayed-first.bin",raw,count) || !snapshot(second,raw,count) || !write_bytes(folder,"second.bin",raw,count))goto done;
    mach_port_t first_name=p1;
    if(mach_port_deallocate(mach_task_self(),p1))goto done;p1=MACH_PORT_NULL;
    if(!send_refs(p2,1))goto done;
    uint32_t first_lookup_after_release=lookup_id(first_name),remaining_lookup=lookup_id(p2);
    if(!send_refs(p2,1))goto done;
    mach_port_t released=p2;if(mach_port_deallocate(mach_task_self(),p2) || !no_send_refs(released))goto done;p2=MACH_PORT_NULL;
    uint32_t retired_second_lookup=lookup_id(released),retired_first_lookup=lookup_id(first_name);
    if(!no_send_refs(released) || !no_send_refs(first_name))goto done;
    // CF aliases remain usable after both received rights have been released.
    if(!snapshot(first,raw,count) || !write_bytes(folder,"after-right-release.bin",raw,count))goto done;
    char path[4096];if(snprintf(path,sizeof(path),"%s/receiver.json",folder)>=(int)sizeof(path))goto done;
    FILE *file=fopen(path,"w");if(!file)goto done;
    int written=fprintf(file,"{\"receiver_pid\":%d,\"first_id\":%u,\"second_id\":%u,\"audit_peer_verified\":true,\"port_names_equal\":%s,\"first_refs_after_two_imports\":%d,\"second_refs_after_first_release\":1,\"received_rights_released\":true,\"fixture_generations\":[1,2],\"first_lookup_after_release\":%u,\"remaining_lookup\":%u,\"retired_first_lookup\":%u,\"retired_second_lookup\":%u}\n",(int)getpid(),id1,id2,same?"true":"false",same?2:1,first_lookup_after_release,remaining_lookup,retired_first_lookup,retired_second_lookup)>0;
    if(fclose(file) || !written)goto done;
    CFRelease(first);first=NULL;CFRelease(second);second=NULL;
    if(send_ack(remote,3,1))goto done;result=0;
 done:
    if(first)CFRelease(first);if(second)CFRelease(second);
    if(MACH_PORT_VALID(p1))mach_port_deallocate(mach_task_self(),p1);if(MACH_PORT_VALID(p2))mach_port_deallocate(mach_task_self(),p2);
    if(MACH_PORT_VALID(inbox))mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);if(MACH_PORT_VALID(remote))mach_port_deallocate(mach_task_self(),remote);return result;
}
int main(int argc,char **argv) {
    alarm(12);
    if(argc==6 && !strcmp(argv[1],"--reuse-peer")){char *end=NULL;long parent=strtol(argv[3],&end,10);if(!end || *end || parent<=1 || getppid()!=parent)return 2;return reuse_peer(argv[2],(pid_t)parent,argv[4],argv[5]);}
    if(argc!=6)return 2;for(int i=1;i<=3;i++)if(!argv[i][0] || strlen(argv[i])>3 || strspn(argv[i],"0123456789")!=strlen(argv[i]))return 2;
    unsigned width=(unsigned)strtoul(argv[1],NULL,10),height=(unsigned)strtoul(argv[2],NULL,10),seed=(unsigned)strtoul(argv[3],NULL,10),next=(seed+1)&255;
    const char *mode=argv[4];if(!width || width>64 || !height || height>16 || seed>255 || (strcmp(mode,"reuse") && strcmp(mode,"separate")))return 2;int same=!strcmp(mode,"reuse");
    mach_port_t inbox=MACH_PORT_NULL,remote=MACH_PORT_NULL,p1=MACH_PORT_NULL,p2=MACH_PORT_NULL;IOSurfaceRef first=NULL,second=NULL;
    pid_t child=-1;int waited=0,registered=0,result=51;uint8_t raw[LIMIT];char service[128],hex[33],parentPID[32];unsigned char nonce[16];
    arc4random_buf(nonce,sizeof(nonce));for(int i=0;i<16;i++)sprintf(hex+i*2,"%02x",nonce[i]);snprintf(service,sizeof(service),"local.re.surface.%d.%s",getpid(),hex);snprintf(parentPID,sizeof(parentPID),"%d",getpid());
    if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox) || mach_port_insert_right(mach_task_self(),inbox,inbox,MACH_MSG_TYPE_MAKE_SEND) || bootstrap_register(bootstrap_port,service,inbox))goto done;registered=1;
    first=create_surface(width,height,seed);if(!first)goto done;size_t stride=IOSurfaceGetBytesPerRow(first),count=stride*height;
    p1=IOSurfaceCreateMachPort(first);if(!MACH_PORT_VALID(p1) || !snapshot(first,raw,count) || !write_bytes(argv[5],"producer-first.bin",raw,count))goto done;
    child=fork();if(child==0){execl(argv[0],argv[0],"--reuse-peer",service,parentPID,mode,argv[5],NULL);_exit(127);}if(child<0)goto done;
    union receive ready;if(receive_message(&ready,inbox))goto done;
    if(!peer_matches(&ready,child) || ready.ack.h.msgh_size!=sizeof(struct ack) || ready.ack.magic!=MAGIC || ready.ack.stage!=0){mach_msg_destroy(&ready.ack.h);goto done;}remote=ready.ack.h.msgh_remote_port;
    if(!MACH_PORT_VALID(remote) || !transfer_surface(remote,p1,first,seed,1))goto done;
    union receive imported;if(receive_message(&imported,inbox) || !peer_matches(&imported,child) || imported.ack.h.msgh_size!=sizeof(struct ack) || imported.ack.magic!=MAGIC || imported.ack.stage!=1 || imported.ack.value!=1)goto done;
    if(same){second=first;p2=p1;if(IOSurfaceLock(first,0,NULL))goto done;pattern(IOSurfaceGetBaseAddress(first),stride,width,height,next);if(IOSurfaceUnlock(first,0,NULL))goto done;}
    else {second=create_surface(width,height,next);if(!second)goto done;p2=IOSurfaceCreateMachPort(second);if(!MACH_PORT_VALID(p2))goto done;}
    if(!snapshot(second,raw,count) || !write_bytes(argv[5],"producer-next.bin",raw,count) || !transfer_surface(remote,p2,second,next,2))goto done;
    union receive complete;if(receive_message(&complete,inbox) || !peer_matches(&complete,child) || complete.ack.h.msgh_size!=sizeof(struct ack) || complete.ack.magic!=MAGIC || complete.ack.stage!=3 || complete.ack.value!=1)goto done;
    int waitStatus;if(waitpid(child,&waitStatus,0)!=child)goto done;waited=1;if(!WIFEXITED(waitStatus) || WEXITSTATUS(waitStatus)!=0)goto done;
    if(!send_refs(p1,1) || !send_refs(p2,1))goto done;
    uint32_t id1=IOSurfaceGetID(first),id2=IOSurfaceGetID(second);
    if(!remove_rendezvous(&inbox,service))goto done;registered=0;
    if(p2!=p1){if(mach_port_deallocate(mach_task_self(),p2))goto done;p2=MACH_PORT_NULL;}
    if(mach_port_deallocate(mach_task_self(),p1))goto done;p1=MACH_PORT_NULL;p2=MACH_PORT_NULL;
    uint32_t live_id1=global_lookup_id(id1),live_id2=global_lookup_id(id2);
    if(second!=first)CFRelease(second);second=NULL;CFRelease(first);first=NULL;
    uint32_t final_id1=global_lookup_id(id1),final_id2=global_lookup_id(id2);
    usleep(100000);
    uint32_t settled_id1=global_lookup_id(id1),settled_id2=global_lookup_id(id2);
    printf("{\"width\":%u,\"height\":%u,\"seed\":%u,\"next_seed\":%u,\"stride\":%zu,\"mode\":\"%s\",\"sender_pid\":%d,\"receiver_pid\":%d,\"first_id\":%u,\"second_id\":%u,\"audit_peer_verified\":true,\"receiver_exit\":0,\"delayed_read_after_second_import\":true,\"rendezvous_removed\":true,\"sender_rights_released\":true,\"sender_aliases_released\":true,\"live_global_first\":%u,\"live_global_second\":%u,\"final_global_first\":%u,\"final_global_second\":%u,\"settled_global_first\":%u,\"settled_global_second\":%u,\"lookup_delay_us\":100000}\n",width,height,seed,next,stride,mode,(int)getpid(),(int)child,id1,id2,live_id1,live_id2,final_id1,final_id2,settled_id1,settled_id2);result=0;
 done:
    if(child>0 && !waited){kill(child,SIGKILL);waitpid(child,NULL,0);}
    if(registered && !remove_rendezvous(&inbox,service))fail("reuse-rendezvous-cleanup",1);
    if(second && second!=first)CFRelease(second);if(first)CFRelease(first);
    if(MACH_PORT_VALID(p2) && p2!=p1)mach_port_deallocate(mach_task_self(),p2);if(MACH_PORT_VALID(p1))mach_port_deallocate(mach_task_self(),p1);
    if(MACH_PORT_VALID(remote))mach_port_deallocate(mach_task_self(),remote);if(MACH_PORT_VALID(inbox))mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);return result;
}
