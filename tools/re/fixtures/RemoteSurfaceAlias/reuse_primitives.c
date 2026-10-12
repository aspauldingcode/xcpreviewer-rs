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
    size_t width=IOSurfaceGetWidth(first),height=IOSurfaceGetHeight(first),stride=IOSurfaceGetBytesPerRow(first),count=IOSurfaceGetAllocSize(first);
    if(!width || width>64 || !height || height>16 || stride<width*4 || !count || count>LIMIT || IOSurfaceGetAllocSize(second)!=count || IOSurfaceGetWidth(second)!=width || IOSurfaceGetHeight(second)!=height || IOSurfaceGetBytesPerRow(second)!=stride)goto done;
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
