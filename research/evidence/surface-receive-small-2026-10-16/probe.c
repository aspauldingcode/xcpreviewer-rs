// One-task owned receive-size failure/recovery; no external rendezvous or UI.
#define main inherited_surface_main
#include "surface_ipc_probe.c"
#undef main
static unsigned refs(mach_port_t p){mach_port_urefs_t n=0;return mach_port_get_refs(mach_task_self(),p,MACH_PORT_RIGHT_SEND,&n)?UINT32_MAX:n;}
static int queue_count(mach_port_t p){mach_port_status_t s={0};mach_msg_type_number_t n=MACH_PORT_RECEIVE_STATUS_COUNT;return mach_port_get_attributes(mach_task_self(),p,MACH_PORT_RECEIVE_STATUS,(mach_port_info_t)&s,&n)?-1:(int)s.mps_msgcount;}
static kern_return_t remove_sends(mach_port_t p){mach_port_urefs_t n=0;kern_return_t code=mach_port_get_refs(mach_task_self(),p,MACH_PORT_RIGHT_SEND,&n);return code?code:(n?mach_port_mod_refs(mach_task_self(),p,MACH_PORT_RIGHT_SEND,-(mach_port_delta_t)n):KERN_SUCCESS);}
static int run_case(int mode,const char *folder){
 int result=65;IOSurfaceRef surface=NULL,alias=NULL,imported=NULL;mach_port_t endpoint=0,resource=0,received_name=0;union receive message={0};int owns_message=0;
 uint8_t raw[LIMIT];size_t count=0,stride=0;unsigned small_code=0;mach_port_t original_name=0;kern_return_t resource_query_after=0,endpoint_query_after=0;
 surface=create_surface(17,9,49,NULL);if(!surface)goto done;count=IOSurfaceGetAllocSize(surface);stride=IOSurfaceGetBytesPerRow(surface);if(count>LIMIT||!snapshot(surface,raw,count)||!write_bytes(folder,"before.bin",raw,count))goto done;
 resource=IOSurfaceCreateMachPort(surface);original_name=resource;alias=IOSurfaceLookupFromMachPort(resource);if(!alias||refs(resource)!=1)goto done;
 if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&endpoint)||mach_port_insert_right(mach_task_self(),endpoint,endpoint,MACH_MSG_TYPE_MAKE_SEND))goto done;
 struct transfer sent={0};sent.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0)|MACH_MSGH_BITS_COMPLEX;sent.h.msgh_size=sizeof(sent);sent.h.msgh_remote_port=endpoint;sent.h.msgh_id=91;sent.body.msgh_descriptor_count=1;sent.port.name=resource;sent.port.disposition=MACH_MSG_TYPE_COPY_SEND;sent.port.type=MACH_MSG_PORT_DESCRIPTOR;sent.magic=MAGIC;
 if(mach_msg(&sent.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(sent),0,MACH_PORT_NULL,0,MACH_PORT_NULL))goto done;
 int queued_before=queue_count(endpoint);unsigned refs_before=refs(resource);
 if(mode){union receive small={0};small_code=mach_msg(&small.transfer.h,MACH_RCV_MSG|MACH_RCV_TIMEOUT|(mode==1?MACH_RCV_LARGE:0),0,sizeof(mach_msg_header_t),endpoint,0,MACH_PORT_NULL);if(small_code==KERN_SUCCESS){mach_msg_destroy(&small.transfer.h);goto done;}if(small_code!=MACH_RCV_TOO_LARGE)goto done;}
 int queued_after=queue_count(endpoint);unsigned refs_after=refs(resource);if(!snapshot(alias,raw,count)||!write_bytes(folder,"after-small.bin",raw,count))goto done;
 kern_return_t receive_code=mach_msg(&message.transfer.h,MACH_RCV_MSG|MACH_RCV_TIMEOUT,0,sizeof(message),endpoint,0,MACH_PORT_NULL);unsigned refs_received=refs(resource);int imported_observed=0;
 if(receive_code==KERN_SUCCESS){owns_message=1;
  if(message.transfer.h.msgh_size!=sizeof(struct transfer)||!(message.transfer.h.msgh_bits&MACH_MSGH_BITS_COMPLEX)||message.transfer.h.msgh_id!=91||message.transfer.body.msgh_descriptor_count!=1||message.transfer.port.type!=MACH_MSG_PORT_DESCRIPTOR||message.transfer.port.disposition!=MACH_MSG_TYPE_PORT_SEND||message.transfer.magic!=MAGIC)goto done;
  received_name=message.transfer.port.name;imported=IOSurfaceLookupFromMachPort(received_name);if(!imported||IOSurfaceGetID(imported)!=IOSurfaceGetID(surface)||!snapshot(imported,raw,count)||!write_bytes(folder,"received.bin",raw,count))goto done;imported_observed=1;
  mach_msg_destroy(&message.transfer.h);owns_message=0;
 }else if(receive_code==MACH_RCV_TIMED_OUT){if(!snapshot(alias,raw,count)||!write_bytes(folder,"after-empty-receive.bin",raw,count))goto done;}else goto done;
 unsigned refs_destroyed=refs(resource);int queued_final=queue_count(endpoint);
 if(remove_sends(resource)!=KERN_SUCCESS)goto done;resource=MACH_PORT_NULL;mach_port_type_t removed_type=0;resource_query_after=mach_port_type(mach_task_self(),original_name,&removed_type);if(resource_query_after!=KERN_INVALID_NAME)goto done;
 if(remove_sends(endpoint)!=KERN_SUCCESS||mach_port_mod_refs(mach_task_self(),endpoint,MACH_PORT_RIGHT_RECEIVE,-1))goto done;mach_port_t old_endpoint=endpoint;endpoint=MACH_PORT_NULL;endpoint_query_after=mach_port_type(mach_task_self(),old_endpoint,&removed_type);if(endpoint_query_after!=KERN_INVALID_NAME)goto done;
 CFRelease(surface);surface=NULL;if(imported)CFRelease(imported);imported=NULL;if(!snapshot(alias,raw,count)||!write_bytes(folder,"alias-after-cleanup.bin",raw,count))goto done;
 if(printf("{\"pid\":%d,\"mode\":%d,\"small_code\":%u,\"receive_code\":%u,\"imported\":%s,\"transfer_size\":%zu,\"header_size\":%zu,\"queued_before\":%d,\"queued_after\":%d,\"queued_final\":%d,\"refs_before\":%u,\"refs_after\":%u,\"refs_received\":%u,\"refs_destroyed\":%u,\"resource_name\":%u,\"received_name\":%u,\"resource_query_after\":%d,\"endpoint_query_after\":%d,\"remaining_refs\":0,\"endpoint_removed\":true,\"stride\":%zu,\"allocation_bytes\":%zu}\n",getpid(),mode,small_code,receive_code,imported_observed?"true":"false",sizeof(struct transfer),sizeof(mach_msg_header_t),queued_before,queued_after,queued_final,refs_before,refs_after,refs_received,refs_destroyed,original_name,received_name,resource_query_after,endpoint_query_after,stride,count)<0)goto done;result=0;
 done:if(owns_message)mach_msg_destroy(&message.transfer.h);if(resource)remove_sends(resource);if(endpoint){remove_sends(endpoint);mach_port_mod_refs(mach_task_self(),endpoint,MACH_PORT_RIGHT_RECEIVE,-1);}if(imported)CFRelease(imported);if(alias)CFRelease(alias);if(surface)CFRelease(surface);return result;
}
int main(int argc,char **argv){alarm(8);if(dprintf(2,"owned_tree_pid:%d\n",getpid())<=0)return 84;if(argc==3&&!strcmp(argv[1],"--output-control")&&!strcmp(argv[2],"output-valid")){return printf("{\"pid\":%d,\"status\":\"owned_output_control\"}\n",getpid())<0?83:0;}if(argc!=3||strcmp(argv[1],"--fixture"))return 2;for(int i=0;i<3;i++){char path[1024];int n=snprintf(path,sizeof(path),"%s/%s",argv[2],i==2?"small":(i?"large":"control"));if(n<0||(size_t)n>=sizeof(path))return 2;int code=run_case(i,path);if(code)return code;}return fflush(stdout)==0&&!ferror(stdout)?0:83;}
