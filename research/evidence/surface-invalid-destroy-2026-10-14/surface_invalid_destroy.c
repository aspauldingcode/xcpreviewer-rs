// Invalid destination occurs before descriptor copy-in; retain exact dispositions.
#define main inherited_surface_main
#include "surface_ipc_probe.c"
#undef main

static unsigned refs(mach_port_t name,mach_port_right_t right) {
    mach_port_urefs_t count=0;
    return mach_port_get_refs(mach_task_self(),name,right,&count)?0:count;
}
int main(int argc,char **argv) {
    alarm(5);if(argc!=3 || (strcmp(argv[1],"copy") && strcmp(argv[1],"move")))return 2;
    int move=!strcmp(argv[1],"move"),result=62;
    IOSurfaceRef surface=NULL,alias=NULL;
    mach_port_t inbox=0,resource=0;
    uint8_t raw[LIMIT];
    surface=create_surface(17,9,49,NULL);if(!surface)goto done;
    size_t count=IOSurfaceGetAllocSize(surface),stride=IOSurfaceGetBytesPerRow(surface);
    if(count>LIMIT || !snapshot(surface,raw,count) || !write_bytes(argv[2],"before.bin",raw,count))goto done;
    resource=IOSurfaceCreateMachPort(surface);alias=IOSurfaceLookupFromMachPort(resource);
    if(!alias || refs(resource,MACH_PORT_RIGHT_SEND)!=1)goto done;
    if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox) || mach_port_insert_right(mach_task_self(),inbox,inbox,MACH_MSG_TYPE_MAKE_SEND))goto done;
    if(mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1))goto done;
    unsigned dead_before=refs(inbox,MACH_PORT_RIGHT_DEAD_NAME);
    struct transfer message={0};message.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0)|MACH_MSGH_BITS_COMPLEX;message.h.msgh_size=sizeof(message);message.h.msgh_remote_port=inbox;message.body.msgh_descriptor_count=1;message.port.name=resource;message.port.type=MACH_MSG_PORT_DESCRIPTOR;message.port.disposition=move?MACH_MSG_TYPE_MOVE_SEND:MACH_MSG_TYPE_COPY_SEND;
    kern_return_t observed=mach_msg(&message.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(message),0,MACH_PORT_NULL,0,MACH_PORT_NULL);
    unsigned before=refs(resource,MACH_PORT_RIGHT_SEND),disposition=message.port.disposition,remote_type=MACH_MSGH_BITS_REMOTE(message.h.msgh_bits);
    mach_port_t returned=message.port.name,original=resource;
    if(!snapshot(alias,raw,count) || !write_bytes(argv[2],"after-invalid-dest.bin",raw,count))goto done;
    mach_msg_destroy(&message.h);
    unsigned after=refs(resource,MACH_PORT_RIGHT_SEND),dead_after=refs(inbox,MACH_PORT_RIGHT_DEAD_NAME);
    if(after && mach_port_mod_refs(mach_task_self(),resource,MACH_PORT_RIGHT_SEND,-(mach_port_delta_t)after))goto done;
    resource=0;
    if(dead_after && mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_DEAD_NAME,-(mach_port_delta_t)dead_after))goto done;
    inbox=0;CFRelease(surface);surface=NULL;
    if(!snapshot(alias,raw,count) || !write_bytes(argv[2],"alias-after-cleanup.bin",raw,count))goto done;
    printf("{\"move\":%s,\"pid\":%d,\"send_code\":%u,\"invalid_dest_constant\":%u,\"original_name\":%u,\"returned_name\":%u,\"returned_disposition\":%u,\"remote_type\":%u,\"resource_refs_before_destroy\":%u,\"resource_refs_after_destroy\":%u,\"dead_refs_before\":%u,\"dead_refs_after_destroy\":%u,\"explicit_remaining_rights_removed\":true,\"alias_survives\":true,\"stride\":%zu,\"allocation_bytes\":%zu}\n",move?"true":"false",getpid(),observed,MACH_SEND_INVALID_DEST,original,returned,disposition,remote_type,before,after,dead_before,dead_after,stride,count);
    result=0;
done:
    if(MACH_PORT_VALID(resource)){unsigned n=refs(resource,MACH_PORT_RIGHT_SEND);if(n)mach_port_mod_refs(mach_task_self(),resource,MACH_PORT_RIGHT_SEND,-(mach_port_delta_t)n);}
    if(MACH_PORT_VALID(inbox)){unsigned n=refs(inbox,MACH_PORT_RIGHT_DEAD_NAME);if(n)mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_DEAD_NAME,-(mach_port_delta_t)n);}
    if(alias)CFRelease(alias);if(surface)CFRelease(surface);
    return result;
}
