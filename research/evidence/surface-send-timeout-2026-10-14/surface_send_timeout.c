// Owned task queue saturation: measure failed COPY_SEND/MOVE_SEND restoration.
#define main inherited_surface_main
#include "surface_ipc_probe.c"
#undef main

static unsigned refs(mach_port_t port) {
    mach_port_urefs_t n=0;
    if(mach_port_get_refs(mach_task_self(),port,MACH_PORT_RIGHT_SEND,&n))return 0;
    return n;
}

static int run_case(const char *folder,int move) {
    IOSurfaceRef surface=create_surface(17,9,49,NULL),alias=NULL;
    mach_port_t inbox=MACH_PORT_NULL,resource=MACH_PORT_NULL;
    int result=60;uint8_t raw[LIMIT];
    if(!surface)goto done;
    size_t count=IOSurfaceGetAllocSize(surface),stride=IOSurfaceGetBytesPerRow(surface);
    if(count>LIMIT || !snapshot(surface,raw,count) || !write_bytes(folder,"before.bin",raw,count))goto done;
    resource=IOSurfaceCreateMachPort(surface);alias=IOSurfaceLookupFromMachPort(resource);
    if(!alias || refs(resource)!=1)goto done;
    if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox) || mach_port_insert_right(mach_task_self(),inbox,inbox,MACH_MSG_TYPE_MAKE_SEND))goto done;
    mach_port_limits_t limit={.mpl_qlimit=1};
    if(mach_port_set_attributes(mach_task_self(),inbox,MACH_PORT_LIMITS_INFO,(mach_port_info_t)&limit,MACH_PORT_LIMITS_INFO_COUNT))goto done;
    struct ack filler={0};filler.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0);filler.h.msgh_size=sizeof(filler);filler.h.msgh_remote_port=inbox;filler.h.msgh_id=77;
    if(mach_msg(&filler.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(filler),0,MACH_PORT_NULL,0,MACH_PORT_NULL))goto done;
    struct transfer transfer={0};transfer.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0)|MACH_MSGH_BITS_COMPLEX;transfer.h.msgh_size=sizeof(transfer);transfer.h.msgh_remote_port=inbox;transfer.h.msgh_id=78;transfer.body.msgh_descriptor_count=1;transfer.port.name=resource;transfer.port.type=MACH_MSG_PORT_DESCRIPTOR;transfer.port.disposition=move?MACH_MSG_TYPE_MOVE_SEND:MACH_MSG_TYPE_COPY_SEND;
    kern_return_t observed=mach_msg(&transfer.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(transfer),0,MACH_PORT_NULL,0,MACH_PORT_NULL);
    unsigned resource_refs=refs(resource),inbox_refs=refs(inbox);
    mach_port_status_t status={0};mach_msg_type_number_t status_count=MACH_PORT_RECEIVE_STATUS_COUNT;
    if(mach_port_get_attributes(mach_task_self(),inbox,MACH_PORT_RECEIVE_STATUS,(mach_port_info_t)&status,&status_count))goto done;
    union receive received;
    if(receive_message(&received,inbox) || received.ack.h.msgh_id!=77)goto done;
    mach_msg_destroy(&received.ack.h);
    memset(&received,0,sizeof(received));
    kern_return_t empty=mach_msg(&received.ack.h,MACH_RCV_MSG|MACH_RCV_TIMEOUT,0,sizeof(received),inbox,0,MACH_PORT_NULL);
    if(!snapshot(alias,raw,count) || !write_bytes(folder,"after-timeout.bin",raw,count))goto done;
    if(resource_refs && mach_port_mod_refs(mach_task_self(),resource,MACH_PORT_RIGHT_SEND,-(mach_port_delta_t)resource_refs))goto done;
    mach_port_type_t type=0;int resource_removed=mach_port_type(mach_task_self(),resource,&type)==KERN_INVALID_NAME;
    resource=MACH_PORT_NULL;
    if(inbox_refs && mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_SEND,-(mach_port_delta_t)inbox_refs))goto done;
    if(mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1))goto done;
    inbox=MACH_PORT_NULL;CFRelease(surface);surface=NULL;
    if(!snapshot(alias,raw,count) || !write_bytes(folder,"alias-after-right-release.bin",raw,count))goto done;
    printf("{\"move\":%s,\"pid\":%d,\"send_code\":%u,\"timeout_constant\":%u,\"resource_refs_after_failure\":%u,\"endpoint_refs_after_failure\":%u,\"returned_disposition\":%u,\"queue_count\":%u,\"queue_limit\":%u,\"empty_receive_code\":%u,\"empty_receive_constant\":%u,\"resource_name_removed\":%s,\"endpoint_removed\":true,\"alias_survives\":true,\"width\":17,\"height\":9,\"seed\":49,\"stride\":%zu,\"allocation_bytes\":%zu}\n",move?"true":"false",getpid(),observed,MACH_SEND_TIMED_OUT,resource_refs,inbox_refs,transfer.port.disposition,status.mps_msgcount,status.mps_qlimit,empty,MACH_RCV_TIMED_OUT,resource_removed?"true":"false",stride,count);
    result=0;
done:
    if(MACH_PORT_VALID(resource)) {unsigned n=refs(resource);if(n)mach_port_mod_refs(mach_task_self(),resource,MACH_PORT_RIGHT_SEND,-(mach_port_delta_t)n);}
    if(MACH_PORT_VALID(inbox))mach_port_destroy(mach_task_self(),inbox);
    if(alias)CFRelease(alias);if(surface)CFRelease(surface);
    return result;
}

int main(int argc,char **argv) {
    alarm(5);if(argc!=3 || (strcmp(argv[1],"copy") && strcmp(argv[1],"move")))return 2;
    return run_case(argv[2],!strcmp(argv[1],"move"));
}
