// Retry the actual returned failed envelope, without rebuilding descriptor names.
#define main inherited_surface_main
#include "surface_ipc_probe.c"
#undef main

static unsigned refs(mach_port_t name) {
    mach_port_urefs_t n=0;
    return mach_port_get_refs(mach_task_self(),name,MACH_PORT_RIGHT_SEND,&n)?0:n;
}
static void remove_sends(mach_port_t *names,unsigned count) {
    for(unsigned i=0;i<count;i++) {
        int duplicate=0;for(unsigned j=0;j<i;j++)if(names[j]==names[i])duplicate=1;
        if(!duplicate && MACH_PORT_VALID(names[i])) {
            unsigned n=refs(names[i]);
            if(n)mach_port_mod_refs(mach_task_self(),names[i],MACH_PORT_RIGHT_SEND,-(mach_port_delta_t)n);
        }
    }
}
int main(int argc,char **argv) {
    alarm(5);if(argc!=3 || (strcmp(argv[1],"copy") && strcmp(argv[1],"move")))return 2;
    int move=!strcmp(argv[1],"move"),result=61;
    IOSurfaceRef surface=NULL,alias=NULL,imported=NULL;
    mach_port_t inbox=0,resource=0,returned=0,received_name=0;
    uint8_t bytes[LIMIT];union receive received;
    surface=create_surface(17,9,49,NULL);if(!surface)goto done;
    size_t count=IOSurfaceGetAllocSize(surface),stride=IOSurfaceGetBytesPerRow(surface);
    if(count>LIMIT || !snapshot(surface,bytes,count) || !write_bytes(argv[2],"before.bin",bytes,count))goto done;
    uint32_t id=IOSurfaceGetID(surface);
    resource=IOSurfaceCreateMachPort(surface);alias=IOSurfaceLookupFromMachPort(resource);
    if(!alias || refs(resource)!=1)goto done;
    if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox) || mach_port_insert_right(mach_task_self(),inbox,inbox,MACH_MSG_TYPE_MAKE_SEND))goto done;
    mach_port_limits_t limits={.mpl_qlimit=1};
    if(mach_port_set_attributes(mach_task_self(),inbox,MACH_PORT_LIMITS_INFO,(mach_port_info_t)&limits,MACH_PORT_LIMITS_INFO_COUNT))goto done;
    struct ack filler={0};filler.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0);filler.h.msgh_size=sizeof(filler);filler.h.msgh_remote_port=inbox;filler.h.msgh_id=77;
    if(mach_msg(&filler.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(filler),0,MACH_PORT_NULL,0,MACH_PORT_NULL))goto done;
    struct transfer message={0};message.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0)|MACH_MSGH_BITS_COMPLEX;message.h.msgh_size=sizeof(message);message.h.msgh_remote_port=inbox;message.h.msgh_id=78;message.body.msgh_descriptor_count=1;message.port.name=resource;message.port.type=MACH_MSG_PORT_DESCRIPTOR;message.port.disposition=move?MACH_MSG_TYPE_MOVE_SEND:MACH_MSG_TYPE_COPY_SEND;
    kern_return_t timeout=mach_msg(&message.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(message),0,MACH_PORT_NULL,0,MACH_PORT_NULL);
    returned=message.port.name;
    unsigned before_original=refs(resource),before_returned=refs(returned),before_endpoint=refs(inbox),returned_disposition=message.port.disposition,returned_remote_type=MACH_MSGH_BITS_REMOTE(message.h.msgh_bits);
    if(timeout!=MACH_SEND_TIMED_OUT || !snapshot(alias,bytes,count) || !write_bytes(argv[2],"after-timeout.bin",bytes,count))goto done;
    if(receive_message(&received,inbox) || received.ack.h.msgh_id!=77)goto done;
    mach_msg_destroy(&received.ack.h);
    // The failed call returned a receive-form envelope with owned MOVE_SEND rights.
    kern_return_t retry=mach_msg(&message.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(message),0,MACH_PORT_NULL,0,MACH_PORT_NULL);
    unsigned after_send_original=refs(resource),after_send_returned=refs(returned),after_send_endpoint=refs(inbox);
    if(retry!=KERN_SUCCESS || receive_message(&received,inbox) || received.transfer.h.msgh_id!=78 || received.transfer.body.msgh_descriptor_count!=1 || received.transfer.port.disposition!=MACH_MSG_TYPE_PORT_SEND)goto done;
    received_name=received.transfer.port.name;imported=IOSurfaceLookupFromMachPort(received_name);
    if(!imported || IOSurfaceGetID(imported)!=id || !snapshot(imported,bytes,count) || !write_bytes(argv[2],"received.bin",bytes,count))goto done;
    unsigned after_receive_original=refs(resource),after_receive_imported=refs(received_name);
    mach_msg_destroy(&received.transfer.h);
    unsigned after_destroy_original=refs(resource),after_destroy_imported=refs(received_name);
    mach_port_t names[]={resource,returned,received_name,inbox};remove_sends(names,4);
    for(unsigned i=0;i<4;i++)if(refs(names[i]))goto done;
    if(mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1))goto done;inbox=0;
    CFRelease(surface);surface=NULL;CFRelease(alias);alias=NULL;
    if(!snapshot(imported,bytes,count) || !write_bytes(argv[2],"import-after-cleanup.bin",bytes,count))goto done;
    printf("{\"move\":%s,\"pid\":%d,\"surface_id\":%u,\"timeout_code\":%u,\"retry_code\":%u,\"original_name\":%u,\"returned_name\":%u,\"received_name\":%u,\"returned_disposition\":%u,\"returned_remote_type\":%u,\"before_original\":%u,\"before_returned\":%u,\"before_endpoint\":%u,\"after_send_original\":%u,\"after_send_returned\":%u,\"after_send_endpoint\":%u,\"after_receive_original\":%u,\"after_receive_imported\":%u,\"after_destroy_original\":%u,\"after_destroy_imported\":%u,\"remaining_send_refs\":0,\"endpoint_removed\":true,\"same_surface_id\":true,\"stride\":%zu,\"allocation_bytes\":%zu}\n",move?"true":"false",getpid(),id,timeout,retry,resource,returned,received_name,returned_disposition,returned_remote_type,before_original,before_returned,before_endpoint,after_send_original,after_send_returned,after_send_endpoint,after_receive_original,after_receive_imported,after_destroy_original,after_destroy_imported,stride,count);
    result=0;
done:
    {mach_port_t names[]={resource,returned,received_name,inbox};remove_sends(names,4);}
    if(MACH_PORT_VALID(inbox))mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);
    if(imported)CFRelease(imported);if(alias)CFRelease(alias);if(surface)CFRelease(surface);
    return result;
}
