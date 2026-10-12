// Reuse the reviewed owned-surface primitives; this executable runs only fault controls.
#define main surface_success_main
#include "surface_ipc_probe.c"
#undef main

static int name_gone(mach_port_t name) {
    mach_port_type_t type=0;
    return mach_port_type(mach_task_self(),name,&type)==KERN_INVALID_NAME;
}
static kern_return_t timed_receive(union receive *buffer,mach_port_t port,unsigned timeout) {
    memset(buffer,0,sizeof(*buffer));
    return mach_msg((mach_msg_header_t *)buffer,MACH_RCV_MSG|MACH_RCV_TIMEOUT|MACH_RCV_TRAILER_TYPE(MACH_MSG_TRAILER_FORMAT_0)|MACH_RCV_TRAILER_ELEMENTS(MACH_RCV_TRAILER_AUDIT),0,sizeof(*buffer),port,timeout,MACH_PORT_NULL);
}
static int fault_peer(const char *service,pid_t parent,const char *phase,const char *folder) {
    mach_port_t remote=MACH_PORT_NULL,inbox=MACH_PORT_NULL,resource=MACH_PORT_NULL;
    IOSurfaceRef alias=NULL;uint8_t bytes[LIMIT],expectedBytes[LIMIT];int result=40;
    if(bootstrap_look_up(bootstrap_port,service,&remote) || !MACH_PORT_VALID(remote))goto done;
    if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox))goto done;
    struct ack ready={0};ready.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,MACH_MSG_TYPE_MAKE_SEND);
    ready.h.msgh_size=sizeof(ready);ready.h.msgh_remote_port=remote;ready.h.msgh_local_port=inbox;ready.magic=MAGIC;
    if(mach_msg(&ready.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(ready),0,MACH_PORT_NULL,3000,MACH_PORT_NULL))goto done;
    if(!strcmp(phase,"before-transfer")) {
        union receive proceed;
        if(receive_message(&proceed,inbox) || !peer_matches(&proceed,parent) || proceed.ack.h.msgh_size!=sizeof(struct ack) || proceed.ack.magic!=MAGIC || proceed.ack.stage!=6)goto done;
        mach_port_t old=inbox;
        if(mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1) || !name_gone(old)){fail("peer-inbox-release",1);goto done;}
        inbox=MACH_PORT_NULL;if(send_ack(remote,4,1))goto done;result=41;goto done;
    }
    union receive incoming;if(receive_message(&incoming,inbox))goto done;struct transfer *m=&incoming.transfer;
    if(!peer_matches(&incoming,parent) || m->h.msgh_size!=sizeof(*m) || !(m->h.msgh_bits&MACH_MSGH_BITS_COMPLEX) || m->body.msgh_descriptor_count!=1 || m->port.type!=MACH_MSG_PORT_DESCRIPTOR || m->port.disposition!=MACH_MSG_TYPE_PORT_SEND || m->magic!=MAGIC || !m->width || m->width>64 || !m->height || m->height>16 || m->stride<m->width*4 || (size_t)m->stride*m->height>LIMIT){mach_msg_destroy(&m->h);goto done;}
    resource=m->port.name;alias=IOSurfaceLookupFromMachPort(resource);size_t count=alias?IOSurfaceGetAllocSize(alias):0;if(!count || count>LIMIT)goto done;
    if(!alias || !send_refs(resource,1) || IOSurfaceGetID(alias)!=m->surface_id || IOSurfaceGetWidth(alias)!=m->width || IOSurfaceGetHeight(alias)!=m->height || IOSurfaceGetBytesPerRow(alias)!=m->stride)goto done;
    pattern(expectedBytes,m->stride,m->width,m->height,m->seed,count);
    if(!snapshot(alias,bytes,count) || memcmp(bytes,expectedBytes,count) || !write_bytes(folder,"imported.bin",bytes,count))goto done;
    if(!strcmp(phase,"after-import")) {
        mach_port_t old=resource;if(mach_port_deallocate(mach_task_self(),resource) || !name_gone(old))goto done;resource=MACH_PORT_NULL;
        if(!snapshot(alias,bytes,count) || memcmp(bytes,expectedBytes,count))goto done;CFRelease(alias);alias=NULL;
        old=inbox;if(mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1) || !name_gone(old)){fail("peer-inbox-release",1);goto done;}inbox=MACH_PORT_NULL;
        if(send_ack(remote,4,1))goto done;result=42;goto done;
    }
    // Prove import completed before withholding the expected completion acknowledgement.
    if(send_ack(remote,5,1))goto done;
    if(!strncmp(phase,"late-ack-",9)) {
        union receive proceed;
        if(receive_message(&proceed,inbox) || !peer_matches(&proceed,parent) || proceed.ack.h.msgh_size!=sizeof(struct ack) || proceed.ack.magic!=MAGIC || proceed.ack.stage!=6)goto done;
        if(!send_refs(resource,1))goto done;
        mach_port_t old=resource;
        if(mach_port_deallocate(mach_task_self(),resource) || !name_gone(old))goto done;resource=MACH_PORT_NULL;
        if(!snapshot(alias,bytes,count) || memcmp(bytes,expectedBytes,count) || !write_bytes(folder,"post-timeout.bin",bytes,count))goto done;
        CFRelease(alias);alias=NULL;
        struct ack late={0};late.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0);
        late.h.msgh_size=sizeof(late);late.h.msgh_remote_port=remote;late.magic=MAGIC;late.stage=7;late.value=1;
        kern_return_t observed=mach_msg(&late.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(late),0,MACH_PORT_NULL,3000,MACH_PORT_NULL);
        int closed=!strcmp(phase,"late-ack-closed");
        if(observed!=(closed?MACH_SEND_INVALID_DEST:KERN_SUCCESS))goto done;
        old=inbox;if(mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1) || !name_gone(old))goto done;inbox=MACH_PORT_NULL;
        old=remote;if(mach_port_deallocate(mach_task_self(),remote) || !name_gone(old))goto done;remote=MACH_PORT_NULL;
        char path[1024];if(snprintf(path,sizeof(path),"%s/late-peer.json",folder)>=(int)sizeof(path))goto done;
        FILE *record=fopen(path,"w");if(!record)goto done;
        int written=fprintf(record,"{\"sender_pid\":%d,\"receiver_pid\":%d,\"phase\":\"%s\",\"mach_error\":%u,\"resource_refs_before_cleanup\":1,\"resource_name_removed\":true,\"cf_reference_released\":true,\"inbox_name_removed\":true,\"reply_name_removed\":true}\n",(int)parent,(int)getpid(),phase,(unsigned)observed);
        int close_error=fclose(record);if(written<0 || close_error)goto done;
        result=closed?44:43;goto done;
    }
    for(;;)pause();
 done:
    if(alias)CFRelease(alias);if(MACH_PORT_VALID(resource))mach_port_deallocate(mach_task_self(),resource);
    if(MACH_PORT_VALID(inbox))mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);
    if(MACH_PORT_VALID(remote))mach_port_deallocate(mach_task_self(),remote);return result;
}
static int use_state(unsigned width,unsigned height,unsigned seed,const char *folder) {
    IOSurfaceRef surface=create_surface(width,height,seed,NULL);if(!surface)return 44;
    mach_port_t port=MACH_PORT_NULL;int active=0,result=44;uint8_t bytes[LIMIT],expectedBytes[LIMIT];
    size_t stride=IOSurfaceGetBytesPerRow(surface),count=IOSurfaceGetAllocSize(surface);if(!count || count>LIMIT)goto done;int local[5],global[5];
    local[0]=IOSurfaceGetUseCount(surface);global[0]=!!IOSurfaceIsInUse(surface);
    port=IOSurfaceCreateMachPort(surface);if(!MACH_PORT_VALID(port))goto done;
    local[1]=IOSurfaceGetUseCount(surface);global[1]=!!IOSurfaceIsInUse(surface);
    IOSurfaceIncrementUseCount(surface);active=1;
    local[2]=IOSurfaceGetUseCount(surface);global[2]=!!IOSurfaceIsInUse(surface);
    mach_port_t old=port;if(mach_port_deallocate(mach_task_self(),port) || !name_gone(old))goto done;port=MACH_PORT_NULL;
    local[3]=IOSurfaceGetUseCount(surface);global[3]=!!IOSurfaceIsInUse(surface);
    IOSurfaceDecrementUseCount(surface);active=0;
    local[4]=IOSurfaceGetUseCount(surface);global[4]=!!IOSurfaceIsInUse(surface);
    pattern(expectedBytes,stride,width,height,seed,count);
    if(!snapshot(surface,bytes,count) || memcmp(bytes,expectedBytes,count) || !write_bytes(folder,"not-in-use.bin",bytes,count))goto done;
    printf("{\"phase\":\"use-state\",\"width\":%u,\"height\":%u,\"seed\":%u,\"stride\":%zu,\"local_use_counts\":[%d,%d,%d,%d,%d],\"global_in_use\":[%d,%d,%d,%d,%d],\"mach_port_name_removed\":true,\"cf_reference_retained\":true}\n",width,height,seed,stride,local[0],local[1],local[2],local[3],local[4],global[0],global[1],global[2],global[3],global[4]);result=0;
 done:
    if(active)IOSurfaceDecrementUseCount(surface);if(MACH_PORT_VALID(port))mach_port_deallocate(mach_task_self(),port);CFRelease(surface);return result;
}

static int full_fault_main(int argc,char **argv) {
    alarm(12);
    if(argc==6 && !strcmp(argv[1],"--fault-peer")) {
        char *end=NULL;long parent=strtol(argv[3],&end,10);
        if(!end || *end || parent<=1 || getppid()!=parent)return 2;
        return fault_peer(argv[2],(pid_t)parent,argv[4],argv[5]);
    }
    if(argc!=6)return 2;
    for(int i=1;i<=3;i++)if(!argv[i][0] || strlen(argv[i])>3 || strspn(argv[i],"0123456789")!=strlen(argv[i]))return 2;
    unsigned width=(unsigned)strtoul(argv[1],NULL,10),height=(unsigned)strtoul(argv[2],NULL,10),seed=(unsigned)strtoul(argv[3],NULL,10);
    const char *phase=argv[4];
    if(!strcmp(phase,"use-state") && width && width<=64 && height && height<=16 && seed<=255)return use_state(width,height,seed,argv[5]);
    if(!width || width>64 || !height || height>16 || seed>255 || (strcmp(phase,"before-transfer") && strcmp(phase,"after-import") && strcmp(phase,"before-ack") && strcmp(phase,"late-ack-open") && strcmp(phase,"late-ack-closed")))return 2;
    mach_port_t inbox=MACH_PORT_NULL,remote=MACH_PORT_NULL,resource=MACH_PORT_NULL;IOSurfaceRef surface=NULL;
    pid_t child=-1;int registered=0,waited=0,result=43,waitStatus=0;char service[128],hex[33],parentPID[32];unsigned char nonce[16];
    uint8_t actual[LIMIT],expectedBytes[LIMIT];arc4random_buf(nonce,sizeof(nonce));for(int i=0;i<16;i++)sprintf(hex+i*2,"%02x",nonce[i]);
    snprintf(service,sizeof(service),"local.re.surface.%d.%s",getpid(),hex);snprintf(parentPID,sizeof(parentPID),"%d",getpid());
    if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox) || mach_port_insert_right(mach_task_self(),inbox,inbox,MACH_MSG_TYPE_MAKE_SEND))goto done;
    if(bootstrap_register(bootstrap_port,service,inbox))goto done;registered=1;
    surface=create_surface(width,height,seed,NULL);if(!surface)goto done;size_t stride=IOSurfaceGetBytesPerRow(surface),count=IOSurfaceGetAllocSize(surface);if(!count || count>LIMIT)goto done;
    resource=IOSurfaceCreateMachPort(surface);if(!MACH_PORT_VALID(resource) || !send_refs(resource,1))goto done;
    child=fork();if(child==0){execl(argv[0],argv[0],"--fault-peer",service,parentPID,phase,argv[5],NULL);_exit(127);}if(child<0)goto done;
    union receive ready;if(receive_message(&ready,inbox))goto done;
    if(!peer_matches(&ready,child) || ready.ack.h.msgh_size!=sizeof(struct ack) || ready.ack.magic!=MAGIC || ready.ack.stage!=0){mach_msg_destroy(&ready.ack.h);goto done;}
    remote=ready.ack.h.msgh_remote_port;if(!MACH_PORT_VALID(remote))goto done;
    struct transfer m={0};m.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0)|MACH_MSGH_BITS_COMPLEX;m.h.msgh_size=sizeof(m);m.h.msgh_remote_port=remote;m.h.msgh_id=99;
    m.body.msgh_descriptor_count=1;m.port.name=resource;m.port.disposition=MACH_MSG_TYPE_COPY_SEND;m.port.type=MACH_MSG_PORT_DESCRIPTOR;
    m.magic=MAGIC;m.width=width;m.height=height;m.seed=seed;m.stride=(uint32_t)stride;m.surface_id=IOSurfaceGetID(surface);
    kern_return_t observed=KERN_SUCCESS;
    int late_received=0;
    if(!strcmp(phase,"before-transfer")) {
        if(send_ack(remote,6,1))goto done;
        union receive failed;if(receive_message(&failed,inbox) || !peer_matches(&failed,child) || failed.ack.h.msgh_size!=sizeof(struct ack) || failed.ack.magic!=MAGIC || failed.ack.stage!=4 || failed.ack.value!=1)goto done;
        if(waitpid(child,&waitStatus,0)!=child)goto done;waited=1;
        if(!WIFEXITED(waitStatus) || WEXITSTATUS(waitStatus)!=41){fail("before-transfer-peer-exit",waitStatus);goto done;}
        observed=mach_msg(&m.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(m),0,MACH_PORT_NULL,3000,MACH_PORT_NULL);
        if(observed!=MACH_SEND_INVALID_DEST){fail("closed-endpoint-send",observed);goto done;}
    } else {
        if(mach_msg(&m.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(m),0,MACH_PORT_NULL,3000,MACH_PORT_NULL))goto done;
        union receive state;if(receive_message(&state,inbox) || !peer_matches(&state,child) || state.ack.h.msgh_size!=sizeof(struct ack) || state.ack.magic!=MAGIC || state.ack.value!=1 || state.ack.stage!=(!strcmp(phase,"after-import")?4u:5u))goto done;
        if(!strcmp(phase,"before-ack")) {
            union receive missing;observed=timed_receive(&missing,inbox,250);
            if(observed!=MACH_RCV_TIMED_OUT || kill(child,SIGKILL))goto done;
        }
        if(!strncmp(phase,"late-ack-",9)) {
            union receive missing;observed=timed_receive(&missing,inbox,250);
            if(observed!=MACH_RCV_TIMED_OUT)goto done;
            if(!strcmp(phase,"late-ack-closed")) {
                if(!remove_rendezvous(&inbox,service))goto done;registered=0;
            }
            if(send_ack(remote,6,1))goto done;
            if(!strcmp(phase,"late-ack-open")) {
                union receive late;
                if(receive_message(&late,inbox) || !peer_matches(&late,child) || late.ack.h.msgh_size!=sizeof(struct ack) || late.ack.magic!=MAGIC || late.ack.stage!=7 || late.ack.value!=1)goto done;
                late_received=1;
            }
        }
        if(waitpid(child,&waitStatus,0)!=child)goto done;waited=1;
        if(!strcmp(phase,"after-import")){if(!WIFEXITED(waitStatus) || WEXITSTATUS(waitStatus)!=42)goto done;}
        else if(!strncmp(phase,"late-ack-",9)){if(!WIFEXITED(waitStatus) || WEXITSTATUS(waitStatus)!=(!strcmp(phase,"late-ack-closed")?44:43))goto done;}
        else if(!WIFSIGNALED(waitStatus) || WTERMSIG(waitStatus)!=SIGKILL)goto done;
    }
    if(!send_refs(resource,1)){mach_port_urefs_t refs=0;mach_port_get_refs(mach_task_self(),resource,MACH_PORT_RIGHT_SEND,&refs);fprintf(stderr,"retained refs=%u disposition=%u bits=%u\n",refs,m.port.disposition,m.h.msgh_bits);goto done;}pattern(expectedBytes,stride,width,height,seed,count);
    if(!snapshot(surface,actual,count) || memcmp(actual,expectedBytes,count) || !write_bytes(argv[5],"retained.bin",actual,count))goto done;
    CFRelease(surface);surface=NULL;mach_port_t old=resource;if(mach_port_deallocate(mach_task_self(),resource) || !name_gone(old))goto done;resource=MACH_PORT_NULL;
    old=remote;if(mach_port_deallocate(mach_task_self(),remote) || !name_gone(old))goto done;remote=MACH_PORT_NULL;
    if(registered && !remove_rendezvous(&inbox,service))goto done;registered=0;
    printf("{\"phase\":\"%s\",\"width\":%u,\"height\":%u,\"seed\":%u,\"stride\":%zu,\"allocation_bytes\":%zu,\"sender_pid\":%d,\"receiver_pid\":%d,\"audit_peer_verified\":true,\"completion_accepted\":false,\"failure_observed\":true,\"mach_error\":%u,\"peer_exit\":%d,\"peer_signal\":%d,\"local_resource_refs_retained\":1,\"local_resource_name_removed\":true,\"peer_endpoint_name_removed\":true,\"rendezvous_removed\":true,\"receiver_cleanup\":\"%s\",\"late_ack_received\":%s}\n",phase,width,height,seed,stride,count,(int)getpid(),(int)child,(unsigned)observed,WIFEXITED(waitStatus)?WEXITSTATUS(waitStatus):-1,WIFSIGNALED(waitStatus)?WTERMSIG(waitStatus):0,!strcmp(phase,"before-ack")?"process-teardown":"explicit",late_received?"true":"false");result=0;
 done:
    if(child>0 && !waited){kill(child,SIGKILL);waitpid(child,NULL,0);}
    if(registered && !remove_rendezvous(&inbox,service))fail("fault-rendezvous-cleanup",1);
    if(surface)CFRelease(surface);if(MACH_PORT_VALID(resource))mach_port_deallocate(mach_task_self(),resource);
    if(MACH_PORT_VALID(remote))mach_port_deallocate(mach_task_self(),remote);
    if(MACH_PORT_VALID(inbox))mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);return result;
}

int main(int argc,char **argv) {
    if(argc==6 && !strcmp(argv[1],"--fault-peer"))return full_fault_main(argc,argv);
    if(argc!=6 || strcmp(argv[4],"batch"))return 2;
    const char *phases[]={"after-import","before-ack"};
    for(unsigned i=0;i<2;i++) {
        char folder[4096];if(snprintf(folder,sizeof(folder),"%s/%s",argv[5],phases[i])>=(int)sizeof(folder))return 2;
        char *args[]={argv[0],argv[1],argv[2],argv[3],(char *)phases[i],folder,NULL};
        int result=full_fault_main(6,args);if(result)return result;
    }
    return 0;
}
