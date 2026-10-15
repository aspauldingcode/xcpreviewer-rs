// Earlier valid resource descriptor followed by an owned receive-only name.
#define main inherited_surface_main
#include "surface_ipc_probe.c"
#undef main
struct pair_message {mach_msg_header_t h;mach_msg_body_t body;mach_msg_port_descriptor_t ports[2];};
static unsigned refs(mach_port_t name) {mach_port_urefs_t n=0;return mach_port_get_refs(mach_task_self(),name,MACH_PORT_RIGHT_SEND,&n)?0:n;}
static void remove_send(mach_port_t name) {unsigned n=refs(name);if(n)mach_port_mod_refs(mach_task_self(),name,MACH_PORT_RIGHT_SEND,-(mach_port_delta_t)n);}
int main(int argc,char **argv) {
    alarm(5);if(argc!=3 || (strcmp(argv[1],"copy") && strcmp(argv[1],"move")))return 2;
    int move=!strcmp(argv[1],"move"),result=63;
    IOSurfaceRef surface=NULL,alias=NULL;mach_port_t endpoint=0,invalid=0,resource=0,returned=0;
    uint8_t raw[LIMIT];surface=create_surface(17,9,49,NULL);if(!surface)goto done;
    size_t count=IOSurfaceGetAllocSize(surface),stride=IOSurfaceGetBytesPerRow(surface);
    if(count>LIMIT || !snapshot(surface,raw,count) || !write_bytes(argv[2],"before.bin",raw,count))goto done;
    resource=IOSurfaceCreateMachPort(surface);alias=IOSurfaceLookupFromMachPort(resource);if(!alias || refs(resource)!=1)goto done;
    if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&endpoint) || mach_port_insert_right(mach_task_self(),endpoint,endpoint,MACH_MSG_TYPE_MAKE_SEND) || mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&invalid))goto done;
    mach_port_type_t invalid_type=0;if(mach_port_type(mach_task_self(),invalid,&invalid_type))goto done;
    struct pair_message m={0};m.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0)|MACH_MSGH_BITS_COMPLEX;m.h.msgh_size=sizeof(m);m.h.msgh_remote_port=endpoint;m.body.msgh_descriptor_count=2;
    m.ports[0].name=resource;m.ports[0].disposition=move?MACH_MSG_TYPE_MOVE_SEND:MACH_MSG_TYPE_COPY_SEND;m.ports[0].type=MACH_MSG_PORT_DESCRIPTOR;
    m.ports[1].name=invalid;m.ports[1].disposition=MACH_MSG_TYPE_MOVE_SEND;m.ports[1].type=MACH_MSG_PORT_DESCRIPTOR;
    kern_return_t observed=mach_msg(&m.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(m),0,MACH_PORT_NULL,0,MACH_PORT_NULL);
    returned=m.ports[0].name;unsigned before_original=refs(resource),before_returned=refs(returned),before_endpoint=refs(endpoint),first_disposition=m.ports[0].disposition,second_disposition=m.ports[1].disposition,remote_type=MACH_MSGH_BITS_REMOTE(m.h.msgh_bits);
    mach_port_t second_name=m.ports[1].name;
    if(!snapshot(alias,raw,count) || !write_bytes(argv[2],"after-error.bin",raw,count))goto done;
    union receive message={0};kern_return_t receive_code=mach_msg(&message.ack.h,MACH_RCV_MSG|MACH_RCV_TIMEOUT,0,sizeof(message),endpoint,0,MACH_PORT_NULL);
    if(receive_code==KERN_SUCCESS)mach_msg_destroy(&message.ack.h);
    mach_msg_destroy(&m.h);
    unsigned after_original=refs(resource),after_returned=refs(returned),after_endpoint=refs(endpoint);mach_port_type_t invalid_after=0;kern_return_t invalid_query=mach_port_type(mach_task_self(),invalid,&invalid_after);
    remove_send(resource);if(returned!=resource)remove_send(returned);remove_send(endpoint);
    if(mach_port_mod_refs(mach_task_self(),endpoint,MACH_PORT_RIGHT_RECEIVE,-1) || mach_port_mod_refs(mach_task_self(),invalid,MACH_PORT_RIGHT_RECEIVE,-1))goto done;
    endpoint=0;invalid=0;CFRelease(surface);surface=NULL;
    if(!snapshot(alias,raw,count) || !write_bytes(argv[2],"alias-after-cleanup.bin",raw,count))goto done;
    printf("{\"move\":%s,\"pid\":%d,\"send_code\":%u,\"invalid_right_constant\":%u,\"original_name\":%u,\"returned_name\":%u,\"second_name\":%u,\"first_disposition\":%u,\"second_disposition\":%u,\"remote_type\":%u,\"before_original\":%u,\"before_returned\":%u,\"before_endpoint\":%u,\"after_original\":%u,\"after_returned\":%u,\"after_endpoint\":%u,\"invalid_type_before\":%u,\"invalid_query_after\":%u,\"invalid_type_after\":%u,\"empty_receive_code\":%u,\"explicit_cleanup\":true,\"stride\":%zu,\"allocation_bytes\":%zu}\n",move?"true":"false",getpid(),observed,MACH_SEND_INVALID_RIGHT,resource,returned,second_name,first_disposition,second_disposition,remote_type,before_original,before_returned,before_endpoint,after_original,after_returned,after_endpoint,invalid_type,invalid_query,invalid_after,receive_code,stride,count);
    result=0;
done:
    remove_send(resource);if(returned!=resource)remove_send(returned);
    if(MACH_PORT_VALID(endpoint)){remove_send(endpoint);mach_port_mod_refs(mach_task_self(),endpoint,MACH_PORT_RIGHT_RECEIVE,-1);}
    if(MACH_PORT_VALID(invalid))mach_port_mod_refs(mach_task_self(),invalid,MACH_PORT_RIGHT_RECEIVE,-1);
    if(alias)CFRelease(alias);if(surface)CFRelease(surface);return result;
}
