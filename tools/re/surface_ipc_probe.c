// Owned fork/exec peers and one random, temporary rendezvous name. Audit-verified peers only.
#include <IOSurface/IOSurface.h>
#include <CoreFoundation/CoreFoundation.h>
#include <mach/mach.h>
#include <servers/bootstrap.h>
#include <bsm/libbsm.h>
#include <sys/wait.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <signal.h>
#include <time.h>

#define MAGIC 0x52455346u
#define LIMIT 65536u
struct transfer {mach_msg_header_t h;mach_msg_body_t body;mach_msg_port_descriptor_t port;uint32_t magic,width,height,seed,stride,surface_id;};
struct ack {mach_msg_header_t h;uint32_t magic,stage,value;};
union receive {struct transfer transfer;struct ack ack;uint8_t storage[sizeof(struct transfer)+MAX_TRAILER_SIZE+32];};

static void fail(const char *phase,int code) {fprintf(stderr,"%s: %d\n",phase,code);}
static kern_return_t receive_message(union receive *buffer,mach_port_t port) {
    memset(buffer,0,sizeof(*buffer));return mach_msg((mach_msg_header_t *)buffer,MACH_RCV_MSG|MACH_RCV_TIMEOUT|MACH_RCV_TRAILER_TYPE(MACH_MSG_TRAILER_FORMAT_0)|MACH_RCV_TRAILER_ELEMENTS(MACH_RCV_TRAILER_AUDIT),0,sizeof(*buffer),port,3000,MACH_PORT_NULL);
}
static int peer_matches(union receive *buffer,pid_t expected) {
    mach_msg_header_t *h=(mach_msg_header_t *)buffer;size_t offset=(h->msgh_size+3u)&~3u;
    if(offset+sizeof(mach_msg_audit_trailer_t)>sizeof(*buffer))return 0;
    mach_msg_audit_trailer_t *t=(void *)(buffer->storage+offset);
    return t->msgh_trailer_type==MACH_MSG_TRAILER_FORMAT_0 && t->msgh_trailer_size>=sizeof(*t) && audit_token_to_pid(t->msgh_audit)==expected;
}
static int send_ack(mach_port_t port,uint32_t stage,uint32_t value) {
    struct ack m={0};m.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0);m.h.msgh_size=sizeof(m);m.h.msgh_remote_port=port;m.h.msgh_id=100+stage;m.magic=MAGIC;m.stage=stage;m.value=value;
    return mach_msg(&m.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(m),0,MACH_PORT_NULL,3000,MACH_PORT_NULL);
}
static void pattern(uint8_t *bytes,size_t stride,size_t width,size_t height,unsigned seed) {
    memset(bytes,0xa5,stride*height);
    for(size_t y=0;y<height;y++)for(size_t x=0;x<width;x++)for(size_t c=0;c<4;c++)bytes[y*stride+x*4+c]=c==3?255:(seed+x*17+y*31+c*53)&255;
}
static IOSurfaceRef create_surface(size_t width,size_t height,unsigned seed) {
    CFStringRef keys[]={kIOSurfaceWidth,kIOSurfaceHeight,kIOSurfaceBytesPerElement,kIOSurfacePixelFormat};
    int32_t values[]={(int32_t)width,(int32_t)height,4,0x42475241};CFNumberRef numbers[4];
    for(int i=0;i<4;i++)numbers[i]=CFNumberCreate(NULL,kCFNumberSInt32Type,&values[i]);
    CFDictionaryRef props=CFDictionaryCreate(NULL,(const void **)keys,(const void **)numbers,4,&kCFTypeDictionaryKeyCallBacks,&kCFTypeDictionaryValueCallBacks);
    IOSurfaceRef surface=IOSurfaceCreate(props);CFRelease(props);for(int i=0;i<4;i++)CFRelease(numbers[i]);
    if(!surface)return NULL;
    size_t stride=IOSurfaceGetBytesPerRow(surface),allocation=IOSurfaceGetAllocSize(surface);
    if(stride<width*4 || stride*height>LIMIT || allocation<stride*height || allocation>1024*1024){CFRelease(surface);return NULL;}
    if(IOSurfaceLock(surface,0,NULL)!=KERN_SUCCESS){CFRelease(surface);return NULL;}
    memset(IOSurfaceGetBaseAddress(surface),0xa5,allocation);pattern(IOSurfaceGetBaseAddress(surface),stride,width,height,seed);
    if(IOSurfaceUnlock(surface,0,NULL)!=KERN_SUCCESS){CFRelease(surface);return NULL;}return surface;
}
static int snapshot(IOSurfaceRef surface,uint8_t *bytes,size_t count) {
    if(IOSurfaceLock(surface,kIOSurfaceLockReadOnly,NULL)!=KERN_SUCCESS)return 0;
    memcpy(bytes,IOSurfaceGetBaseAddress(surface),count);return IOSurfaceUnlock(surface,kIOSurfaceLockReadOnly,NULL)==KERN_SUCCESS;
}
static int mutate(IOSurfaceRef surface,size_t offset,uint8_t bits) {
    if(IOSurfaceLock(surface,0,NULL)!=KERN_SUCCESS)return 0;
    ((uint8_t *)IOSurfaceGetBaseAddress(surface))[offset]^=bits;return IOSurfaceUnlock(surface,0,NULL)==KERN_SUCCESS;
}
static int write_bytes(const char *folder,const char *name,const uint8_t *bytes,size_t count) {
    char path[4096];if(snprintf(path,sizeof(path),"%s/%s",folder,name)>=(int)sizeof(path))return 0;
    FILE *file=fopen(path,"wb");if(!file)return 0;int ok=fwrite(bytes,1,count,file)==count;return fclose(file)==0 && ok;
}
static int remove_rendezvous(mach_port_t *inbox,const char *service) {
    if(!MACH_PORT_VALID(*inbox))return 0;
    if(mach_port_mod_refs(mach_task_self(),*inbox,MACH_PORT_RIGHT_RECEIVE,-1)!=KERN_SUCCESS)return 0;
    mach_port_deallocate(mach_task_self(),*inbox);*inbox=MACH_PORT_NULL;
    for(int i=0;i<100;i++) {
        mach_port_t found=MACH_PORT_NULL;int code=bootstrap_look_up(bootstrap_port,service,&found);
        if(code==BOOTSTRAP_UNKNOWN_SERVICE)return 1;
        if(MACH_PORT_VALID(found))mach_port_deallocate(mach_task_self(),found);
        struct timespec pause={0,10000000};nanosleep(&pause,NULL);
    }
    return 0;
}
static int sender(unsigned width,unsigned height,unsigned seed,int abrupt,pid_t parent,const char *service) {
    fprintf(stderr,"sender: started\n");
    mach_port_t rendezvous=MACH_PORT_NULL;
    int status=bootstrap_look_up(bootstrap_port,service,&rendezvous);
    if(status || !MACH_PORT_VALID(rendezvous)){fail("rendezvous-lookup",status);return 10;}
    fprintf(stderr,"sender: rendezvous acquired\n");
    mach_port_t reply=MACH_PORT_NULL;IOSurfaceRef surface=NULL;mach_port_t resource=MACH_PORT_NULL;int result=11;
    if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&reply))goto done;
    fprintf(stderr,"sender: creating surface\n");surface=create_surface(width,height,seed);if(!surface)goto done;fprintf(stderr,"sender: surface created\n");resource=IOSurfaceCreateMachPort(surface);if(!MACH_PORT_VALID(resource))goto done;
    struct transfer m={0};m.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,MACH_MSG_TYPE_MAKE_SEND)|MACH_MSGH_BITS_COMPLEX;m.h.msgh_size=sizeof(m);m.h.msgh_remote_port=rendezvous;m.h.msgh_local_port=reply;m.h.msgh_id=99;
    m.body.msgh_descriptor_count=1;m.port.name=resource;m.port.disposition=MACH_MSG_TYPE_COPY_SEND;m.port.type=MACH_MSG_PORT_DESCRIPTOR;
    m.magic=MAGIC;m.width=width;m.height=height;m.seed=seed;m.stride=(uint32_t)IOSurfaceGetBytesPerRow(surface);m.surface_id=IOSurfaceGetID(surface);
    status=mach_msg(&m.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(m),0,MACH_PORT_NULL,3000,MACH_PORT_NULL);if(status){fail("send-resource",status);goto done;}fprintf(stderr,"sender: resource sent\n");
    union receive received;status=receive_message(&received,reply);
    if(status || !peer_matches(&received,parent) || received.ack.h.msgh_size!=sizeof(struct ack) || received.ack.magic!=MAGIC || received.ack.stage!=1){fail("receiver-ack",status);goto done;}
    size_t count=m.stride*height;uint8_t *expected=malloc(count),*actual=malloc(count);if(!expected || !actual){free(expected);free(actual);goto done;}
    pattern(expected,m.stride,width,height,seed);expected[0]^=0x5a;
    int shared=snapshot(surface,actual,count)&&memcmp(expected,actual,count)==0;free(expected);free(actual);
    status=send_ack(rendezvous,2,shared);if(status || !shared){fail("shared-mutation",status);goto done;}
    if(abrupt)_exit(23);result=0;
 done:
    if(surface)CFRelease(surface);if(MACH_PORT_VALID(resource))mach_port_deallocate(mach_task_self(),resource);
    if(MACH_PORT_VALID(reply))mach_port_mod_refs(mach_task_self(),reply,MACH_PORT_RIGHT_RECEIVE,-1);mach_port_deallocate(mach_task_self(),rendezvous);return result;
}
static int send_refs(mach_port_t port,unsigned expected) {
    mach_port_urefs_t refs=0;
    return mach_port_get_refs(mach_task_self(),port,MACH_PORT_RIGHT_SEND,&refs)==KERN_SUCCESS && refs==expected;
}
static int no_send_refs(mach_port_t port) {
    mach_port_urefs_t refs=0;
    kern_return_t code=mach_port_get_refs(mach_task_self(),port,MACH_PORT_RIGHT_SEND,&refs);
    return code==KERN_INVALID_NAME || code==KERN_INVALID_RIGHT || (code==KERN_SUCCESS && refs==0);
}
static int receiver_child(unsigned width,unsigned height,unsigned seed,int abrupt,pid_t parent,const char *service,const char *folder) {
    mach_port_t remote=MACH_PORT_NULL,inbox=MACH_PORT_NULL,resource=MACH_PORT_NULL;
    IOSurfaceRef alias=NULL;uint8_t *raw=NULL,*expected=NULL;int result=30,status;
    if(bootstrap_look_up(bootstrap_port,service,&remote) || !MACH_PORT_VALID(remote))goto done;
    if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox))goto done;
    struct ack ready={0};ready.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,MACH_MSG_TYPE_MAKE_SEND);
    ready.h.msgh_size=sizeof(ready);ready.h.msgh_remote_port=remote;ready.h.msgh_local_port=inbox;ready.magic=MAGIC;
    if(mach_msg(&ready.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(ready),0,MACH_PORT_NULL,3000,MACH_PORT_NULL))goto done;
    union receive incoming;status=receive_message(&incoming,inbox);if(status){fail("receiver-transfer",status);goto done;}
    struct transfer *m=&incoming.transfer;
    if(!peer_matches(&incoming,parent) || m->h.msgh_size!=sizeof(*m) || !(m->h.msgh_bits&MACH_MSGH_BITS_COMPLEX) || m->body.msgh_descriptor_count!=1 || m->port.type!=MACH_MSG_PORT_DESCRIPTOR || m->port.disposition!=MACH_MSG_TYPE_PORT_SEND || m->magic!=MAGIC || m->width!=width || m->height!=height || m->seed!=seed){mach_msg_destroy(&m->h);goto done;}
    resource=m->port.name;alias=IOSurfaceLookupFromMachPort(resource);
    if(!alias || !send_refs(resource,1) || IOSurfaceGetID(alias)!=m->surface_id || IOSurfaceGetWidth(alias)!=width || IOSurfaceGetHeight(alias)!=height || IOSurfaceGetBytesPerElement(alias)!=4 || IOSurfaceGetPixelFormat(alias)!=0x42475241 || IOSurfaceGetPlaneCount(alias)!=0 || IOSurfaceGetBytesPerRow(alias)!=m->stride || m->stride<width*4 || (size_t)m->stride*height>LIMIT)goto done;
    size_t count=(size_t)m->stride*height;raw=malloc(count);expected=malloc(count);if(!raw || !expected)goto done;
    pattern(expected,m->stride,width,height,seed);
    if(!snapshot(alias,raw,count) || memcmp(raw,expected,count) || !write_bytes(folder,"before.bin",raw,count) || !mutate(alias,0,0x5a))goto done;
    if(abrupt) {
        // Leave the imported right and CF reference live. Process teardown owns cleanup.
        if(send_ack(remote,3,1))goto done;
        _exit(23);
    }
    mach_port_t released=resource;
    if(mach_port_deallocate(mach_task_self(),resource) || !no_send_refs(released))goto done;
    resource=MACH_PORT_NULL;
    expected[0]^=0x5a;
    if(!snapshot(alias,raw,count) || memcmp(raw,expected,count))goto done;
    CFRelease(alias);alias=NULL;
    if(send_ack(remote,3,1))goto done;
    result=0;
 done:
    if(alias)CFRelease(alias);if(MACH_PORT_VALID(resource))mach_port_deallocate(mach_task_self(),resource);
    if(MACH_PORT_VALID(inbox))mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);
    if(MACH_PORT_VALID(remote))mach_port_deallocate(mach_task_self(),remote);
    free(raw);free(expected);return result;
}
static int receiver_first(int argc,char **argv) {
    (void)argc;
    unsigned width=(unsigned)strtoul(argv[1],NULL,10),height=(unsigned)strtoul(argv[2],NULL,10),seed=(unsigned)strtoul(argv[3],NULL,10);
    int abrupt=!strcmp(argv[4],"receiver-abrupt");
    mach_port_t inbox=MACH_PORT_NULL,remote=MACH_PORT_NULL,resource=MACH_PORT_NULL;
    IOSurfaceRef surface=NULL,retained=NULL;pid_t child=-1;int waited=0,registered=0,result=31;
    uint8_t *raw=NULL,*expected=NULL;char service[128],hex[33],parentPID[32];unsigned char nonce[16];
    arc4random_buf(nonce,sizeof(nonce));for(int i=0;i<16;i++)sprintf(hex+i*2,"%02x",nonce[i]);
    snprintf(service,sizeof(service),"local.re.surface.%d.%s",getpid(),hex);snprintf(parentPID,sizeof(parentPID),"%d",getpid());
    if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox) || mach_port_insert_right(mach_task_self(),inbox,inbox,MACH_MSG_TYPE_MAKE_SEND))goto done;
    if(bootstrap_register(bootstrap_port,service,inbox))goto done;registered=1;
    surface=create_surface(width,height,seed);if(!surface)goto done;
    size_t stride=IOSurfaceGetBytesPerRow(surface),count=stride*height;uint32_t surfaceID=IOSurfaceGetID(surface);
    resource=IOSurfaceCreateMachPort(surface);if(!MACH_PORT_VALID(resource) || !send_refs(resource,1))goto done;
    child=fork();if(child==0){execl(argv[0],argv[0],"--receiver",argv[1],argv[2],argv[3],argv[4],parentPID,service,argv[5],NULL);_exit(127);}if(child<0)goto done;
    union receive ready;int status=receive_message(&ready,inbox);
    if(status || !peer_matches(&ready,child) || ready.ack.h.msgh_size!=sizeof(struct ack) || ready.ack.magic!=MAGIC || ready.ack.stage!=0){if(!status)mach_msg_destroy(&ready.ack.h);goto done;}
    remote=ready.ack.h.msgh_remote_port;if(!MACH_PORT_VALID(remote))goto done;
    struct transfer m={0};m.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0)|MACH_MSGH_BITS_COMPLEX;
    m.h.msgh_size=sizeof(m);m.h.msgh_remote_port=remote;m.h.msgh_id=99;m.body.msgh_descriptor_count=1;
    m.port.name=resource;m.port.disposition=MACH_MSG_TYPE_COPY_SEND;m.port.type=MACH_MSG_PORT_DESCRIPTOR;
    m.magic=MAGIC;m.width=width;m.height=height;m.seed=seed;m.stride=(uint32_t)stride;m.surface_id=surfaceID;
    if(mach_msg(&m.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(m),0,MACH_PORT_NULL,3000,MACH_PORT_NULL) || !send_refs(resource,1))goto done;
    union receive confirmation;status=receive_message(&confirmation,inbox);
    if(status || !peer_matches(&confirmation,child) || confirmation.ack.h.msgh_size!=sizeof(struct ack) || confirmation.ack.magic!=MAGIC || confirmation.ack.stage!=3 || confirmation.ack.value!=1)goto done;
    int waitStatus;if(waitpid(child,&waitStatus,0)!=child)goto done;waited=1;
    if(!WIFEXITED(waitStatus) || WEXITSTATUS(waitStatus)!=(abrupt?23:0) || !send_refs(resource,1))goto done;
    raw=malloc(count);expected=malloc(count);if(!raw || !expected)goto done;
    pattern(expected,stride,width,height,seed);expected[0]^=0x5a;
    if(!snapshot(surface,raw,count) || memcmp(raw,expected,count) || !write_bytes(argv[5],"after-exit.bin",raw,count) || !mutate(surface,1,0xa6))goto done;
    expected[1]^=0xa6;if(!snapshot(surface,raw,count) || memcmp(raw,expected,count) || !write_bytes(argv[5],"after-owner-mutation.bin",raw,count))goto done;
    // Drop the original CF reference; the retained Mach right must still provide access.
    CFRelease(surface);surface=NULL;retained=IOSurfaceLookupFromMachPort(resource);
    if(!retained || IOSurfaceGetID(retained)!=surfaceID || !snapshot(retained,raw,count) || memcmp(raw,expected,count) || !write_bytes(argv[5],"port-only.bin",raw,count))goto done;
    CFRelease(retained);retained=NULL;mach_port_t released=resource;
    if(mach_port_deallocate(mach_task_self(),resource) || !no_send_refs(released))goto done;resource=MACH_PORT_NULL;
    if(!remove_rendezvous(&inbox,service))goto done;registered=0;
    printf("{\"width\":%u,\"height\":%u,\"seed\":%u,\"stride\":%zu,\"mode\":\"%s\",\"receiver_exit\":%d,\"sender_pid\":%d,\"receiver_pid\":%d,\"audit_peer_verified\":true,\"different_processes\":true,\"survives_receiver_exit\":true,\"owner_mutation_after_exit\":true,\"port_retains_after_owner_release\":true,\"sender_send_refs_before\":1,\"sender_send_refs_after_copy\":1,\"sender_send_refs_after_exit\":1,\"sender_send_refs_after_release\":0,\"receiver_release\":\"%s\",\"rendezvous_removed\":true}\n",width,height,seed,stride,argv[4],WEXITSTATUS(waitStatus),(int)getpid(),(int)child,abrupt?"process-teardown":"explicit-port-and-cf");result=0;
 done:
    if(child>0 && !waited){kill(child,SIGKILL);waitpid(child,NULL,0);}
    if(registered && !remove_rendezvous(&inbox,service))fail("rendezvous-cleanup",1);
    if(surface)CFRelease(surface);if(retained)CFRelease(retained);
    if(MACH_PORT_VALID(resource))mach_port_deallocate(mach_task_self(),resource);
    if(MACH_PORT_VALID(remote))mach_port_deallocate(mach_task_self(),remote);
    if(MACH_PORT_VALID(inbox))mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);
    free(raw);free(expected);return result;
}

int main(int argc,char **argv) {
    alarm(12);
    int receiverMode=argc==9 && !strcmp(argv[1],"--receiver");
    int childMode=(argc==8 && !strcmp(argv[1],"--sender")) || receiverMode;if(!childMode && argc!=6)return 2;
    int start=childMode?2:1;unsigned values[3];for(int i=0;i<3;i++){const char *s=argv[start+i];if(!s[0]||strlen(s)>3||strspn(s,"0123456789")!=strlen(s))return 2;values[i]=(unsigned)strtoul(s,NULL,10);}
    if(!values[0]||values[0]>64||!values[1]||values[1]>16||values[2]>255)return 2;
    const char *mode=argv[start+3];if(strcmp(mode,"clean") && strcmp(mode,"abrupt") && strcmp(mode,"receiver-clean") && strcmp(mode,"receiver-abrupt"))return 2;int abrupt=!strcmp(mode,"abrupt") || !strcmp(mode,"receiver-abrupt");
    if(childMode){char *end=NULL;long parent=strtol(argv[6],&end,10);if(!end || *end || parent<=1 || getppid()!=parent)return 2;if(receiverMode)return receiver_child(values[0],values[1],values[2],abrupt,(pid_t)parent,argv[7],argv[8]);return sender(values[0],values[1],values[2],abrupt,(pid_t)parent,argv[7]);}
    if(!strncmp(mode,"receiver-",9))return receiver_first(argc,argv);
    mach_port_t inbox=MACH_PORT_NULL,receivedPort=MACH_PORT_NULL,reply=MACH_PORT_NULL;IOSurfaceRef alias=NULL;pid_t child=-1;int waited=0,result=12,status;
    char service[128]={0};unsigned char nonce[16];arc4random_buf(nonce,sizeof(nonce));char hex[33];for(int i=0;i<16;i++)sprintf(hex+i*2,"%02x",nonce[i]);snprintf(service,sizeof(service),"local.re.surface.%d.%s",getpid(),hex);int registered=0;
    uint8_t *before=NULL,*after=NULL,*expected=NULL;union receive incoming;
    if(mach_port_allocate(mach_task_self(),MACH_PORT_RIGHT_RECEIVE,&inbox) || mach_port_insert_right(mach_task_self(),inbox,inbox,MACH_MSG_TYPE_MAKE_SEND))goto done;
    status=bootstrap_register(bootstrap_port,service,inbox);if(status){fail("rendezvous-register",status);goto done;}registered=1;
    char parentPID[32];snprintf(parentPID,sizeof(parentPID),"%d",getpid());child=fork();
    if(child==0){execl(argv[0],argv[0],"--sender",argv[1],argv[2],argv[3],argv[4],parentPID,service,NULL);_exit(127);}
    if(child<0)goto done;
    status=receive_message(&incoming,inbox);if(status){fail("receive-resource",status);goto done;}
    struct transfer *m=&incoming.transfer;
    if(!peer_matches(&incoming,child) || m->h.msgh_size!=sizeof(*m) || !(m->h.msgh_bits&MACH_MSGH_BITS_COMPLEX) || m->body.msgh_descriptor_count!=1 || m->port.type!=MACH_MSG_PORT_DESCRIPTOR || m->port.disposition!=MACH_MSG_TYPE_PORT_SEND || m->magic!=MAGIC || m->width!=values[0] || m->height!=values[1] || m->seed!=values[2]){mach_msg_destroy(&m->h);goto done;}
    receivedPort=m->port.name;reply=m->h.msgh_remote_port;alias=IOSurfaceLookupFromMachPort(receivedPort);
    if(!alias || IOSurfaceGetID(alias)!=m->surface_id || IOSurfaceGetWidth(alias)!=values[0] || IOSurfaceGetHeight(alias)!=values[1] || IOSurfaceGetBytesPerElement(alias)!=4 || IOSurfaceGetPixelFormat(alias)!=0x42475241 || IOSurfaceGetPlaneCount(alias)!=0 || IOSurfaceGetBytesPerRow(alias)!=m->stride || m->stride<values[0]*4 || (size_t)m->stride*values[1]>LIMIT)goto done;
    size_t count=m->stride*values[1];before=malloc(count);after=malloc(count);expected=malloc(count);if(!before || !after || !expected)goto done;pattern(expected,m->stride,values[0],values[1],values[2]);
    if(!snapshot(alias,before,count) || memcmp(before,expected,count) || !write_bytes(argv[5],"before.bin",before,count) || !mutate(alias,0,0x5a))goto done;
    if(mach_port_deallocate(mach_task_self(),receivedPort)!=KERN_SUCCESS)goto done;receivedPort=MACH_PORT_NULL;
    if(send_ack(reply,1,1))goto done;
    union receive confirmation;status=receive_message(&confirmation,inbox);
    if(status || !peer_matches(&confirmation,child) || confirmation.ack.h.msgh_size!=sizeof(struct ack) || confirmation.ack.magic!=MAGIC || confirmation.ack.stage!=2 || confirmation.ack.value!=1)goto done;
    int waitStatus;if(waitpid(child,&waitStatus,0)!=child)goto done;waited=1;
    if(!WIFEXITED(waitStatus) || WEXITSTATUS(waitStatus)!=(abrupt?23:0))goto done;
    expected[0]^=0x5a;if(!snapshot(alias,after,count) || memcmp(after,expected,count) || !write_bytes(argv[5],"after-exit.bin",after,count) || !mutate(alias,1,0xa6))goto done;
    expected[1]^=0xa6;if(!snapshot(alias,after,count) || memcmp(after,expected,count) || !write_bytes(argv[5],"after-receiver-mutation.bin",after,count))goto done;
    if(!remove_rendezvous(&inbox,service)){fail("rendezvous-disappearance",1);goto done;}registered=0;
    printf("{\"width\":%u,\"height\":%u,\"seed\":%u,\"stride\":%u,\"mode\":\"%s\",\"sender_exit\":%d,\"sender_pid\":%d,\"receiver_pid\":%d,\"rendezvous_removed\":true,\"different_processes\":true,\"audit_peer_verified\":true,\"sender_observed_receiver_mutation\":true,\"received_port_released_before_sender_exit\":true,\"survives_sender_exit\":true,\"receiver_mutation_after_exit\":true}\n",values[0],values[1],values[2],m->stride,mode,WEXITSTATUS(waitStatus),(int)child,(int)getpid());result=0;
 done:
    if(registered && !remove_rendezvous(&inbox,service))fail("rendezvous-cleanup",1);
    if(child>0 && !waited){kill(child,SIGKILL);waitpid(child,NULL,0);}if(alias)CFRelease(alias);if(MACH_PORT_VALID(receivedPort))mach_port_deallocate(mach_task_self(),receivedPort);if(MACH_PORT_VALID(reply))mach_port_deallocate(mach_task_self(),reply);if(MACH_PORT_VALID(inbox))mach_port_mod_refs(mach_task_self(),inbox,MACH_PORT_RIGHT_RECEIVE,-1);free(before);free(after);free(expected);return result;
}
