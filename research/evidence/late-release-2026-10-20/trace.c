#include "trace.h"
#include <stdatomic.h>
#include <string.h>
#include <stdlib.h>
#include <dispatch/dispatch.h>
#include <bsm/libbsm.h>
#define LIMIT 256
_Static_assert(sizeof(mach_msg_port_descriptor_t)==12,"owned userspace port descriptor ABI");
static _Atomic unsigned active,count;static _Atomic uint32_t reply_port,header_reply_port,reply_bits;
static unsigned descriptor_order[128],descriptor_order_count;
int trace_set_descriptor_order(const uint32_t *order,unsigned n){if(n>128)return 1;memcpy(descriptor_order,order,n*sizeof(*order));descriptor_order_count=n;return 0;}
static unsigned replacement_size;static unsigned char replacement_body[4096];
int trace_set_replacement(const unsigned char *bytes,unsigned n){if(n>4096)return 1;memcpy(replacement_body,bytes,n);replacement_size=n;return 0;}
static struct TraceRow rows[LIMIT];
static _Atomic unsigned done[LIMIT];
static _Thread_local unsigned depth;
static unsigned enter(uint32_t api,mach_msg_header_t *msg,mach_msg_option_t opt,mach_msg_size_t send,mach_msg_size_t recv,void *caller){
 if(depth++ || !atomic_load(&active)) return LIMIT;
 unsigned i=atomic_fetch_add(&count,1);if(i>=LIMIT)return LIMIT;
 rows[i]=(struct TraceRow){.api=api,.options=opt,.send_size=send,.receive_size=recv,.caller=(uintptr_t)caller};
 if((opt&MACH_SEND_MSG)&&msg&&send>=sizeof(*msg)){rows[i].send_bits=msg->msgh_bits;rows[i].send_id=msg->msgh_id;rows[i].send_body_size=send-sizeof(*msg);if(rows[i].send_body_size>4096)rows[i].send_body_size=4096;memcpy(rows[i].send_body,(unsigned char*)msg+sizeof(*msg),rows[i].send_body_size);}
 return i;
}
static void leave(unsigned i,mach_msg_header_t *recv,mach_msg_option_t opt,mach_msg_size_t cap,mach_msg_return_t result){
 if(i<LIMIT){rows[i].result=result;if(result==MACH_RCV_TOO_LARGE&&(opt&MACH_RCV_LARGE)&&recv&&cap>=sizeof(*recv))rows[i].receive_message_size=recv->msgh_size;if(result==MACH_MSG_SUCCESS&&(opt&MACH_RCV_MSG)&&recv&&cap>=sizeof(*recv)){rows[i].receive_bits=recv->msgh_bits;rows[i].receive_id=recv->msgh_id;rows[i].receive_message_size=recv->msgh_size;if(recv->msgh_size>=sizeof(*recv)&&recv->msgh_size<=cap){rows[i].receive_body_size=recv->msgh_size-sizeof(*recv);if(rows[i].receive_body_size>4096)rows[i].receive_body_size=4096;memcpy(rows[i].receive_body,(unsigned char*)recv+sizeof(*recv),rows[i].receive_body_size);}}if(result==MACH_MSG_SUCCESS&&(opt&MACH_RCV_MSG)&&recv){size_t offset=(recv->msgh_size+3u)&~3u;if(offset+sizeof(mach_msg_audit_trailer_t)<=cap){mach_msg_audit_trailer_t *trailer=(void*)((unsigned char*)recv+offset);if(trailer->msgh_trailer_type==0&&trailer->msgh_trailer_size>=sizeof(*trailer))rows[i].receive_audit_pid=(uint32_t)audit_token_to_pid(trailer->msgh_audit);}}atomic_store_explicit(&done[i],1,memory_order_release);}depth--;
}
static mach_port_t route_target;static int route_export;
void trace_route(mach_port_t target,int export_endpoint){route_target=target;route_export=export_endpoint;}
static mach_msg_return_t traced_msg(mach_msg_header_t *m,mach_msg_option_t o,mach_msg_size_t s,mach_msg_size_t r,mach_port_name_t p,mach_msg_timeout_t t,mach_port_name_t n){static _Thread_local union {mach_msg_header_t header;unsigned char bytes[sizeof(mach_msg_header_t)+4096];} owned;if(replacement_size&&(o&MACH_SEND_MSG)&&m&&m->msgh_id==0x20000000){memcpy(&owned.header,m,sizeof(*m));unsigned prefix=0;if(m->msgh_bits&MACH_MSGH_BITS_COMPLEX){unsigned count=0;memcpy(&count,(unsigned char*)m+sizeof(*m),4);unsigned n=descriptor_order_count?descriptor_order_count:count;if(count>128||n>128||m->msgh_size<sizeof(*m)+4+count*sizeof(mach_msg_port_descriptor_t))abort();prefix=4+n*sizeof(mach_msg_port_descriptor_t);if(prefix+replacement_size>4096)abort();memcpy(owned.bytes+sizeof(*m),&n,4);for(unsigned j=0;j<n;j++){unsigned index=descriptor_order_count?descriptor_order[j]:j;if(index>=count)abort();mach_msg_port_descriptor_t d;memcpy(&d,(unsigned char*)m+sizeof(*m)+4+index*sizeof(d),sizeof(d));if(d.type!=MACH_MSG_PORT_DESCRIPTOR||d.disposition!=MACH_MSG_TYPE_COPY_SEND)abort();memcpy(owned.bytes+sizeof(*m)+4+j*sizeof(mach_msg_port_descriptor_t),(unsigned char*)m+sizeof(*m)+4+index*sizeof(mach_msg_port_descriptor_t),sizeof(mach_msg_port_descriptor_t));}}memcpy(owned.bytes+sizeof(*m)+prefix,replacement_body,replacement_size);owned.header.msgh_size=sizeof(*m)+prefix+replacement_size;m=&owned.header;s=owned.header.msgh_size;}unsigned i=enter(1,m,o,s,r,__builtin_return_address(0));mach_msg_return_t k;
if(route_target&&(o&MACH_SEND_MSG)&&m&&m->msgh_id==0x20000000){
 if((m->msgh_bits&0xff)!=MACH_MSG_TYPE_MOVE_SEND_ONCE||(o&MACH_RCV_MSG))abort();
 if(route_export){struct {mach_msg_header_t h;mach_msg_body_t b;mach_msg_port_descriptor_t p;} transfer={0};transfer.h.msgh_bits=MACH_MSGH_BITS(MACH_MSG_TYPE_COPY_SEND,0)|MACH_MSGH_BITS_COMPLEX;transfer.h.msgh_size=sizeof(transfer);transfer.h.msgh_remote_port=route_target;transfer.h.msgh_id=74;transfer.b.msgh_descriptor_count=1;transfer.p.name=m->msgh_remote_port;transfer.p.type=MACH_MSG_PORT_DESCRIPTOR;transfer.p.disposition=MACH_MSG_TYPE_MOVE_SEND_ONCE;k=mach_msg(&transfer.h,MACH_SEND_MSG|MACH_SEND_TIMEOUT,sizeof(transfer),0,0,500,0);}
 else {if(mach_port_deallocate(mach_task_self(),m->msgh_remote_port))abort();m->msgh_remote_port=route_target;k=mach_msg(m,o|MACH_SEND_TIMEOUT,s,r,p,500,n);}
 route_target=0;
}else k=mach_msg(m,o,s,r,p,t,n);leave(i,m,o,r,k);return k;}
static mach_msg_return_t traced_overwrite(mach_msg_header_t *m,mach_msg_option_t o,mach_msg_size_t s,mach_msg_size_t r,mach_port_name_t p,mach_msg_timeout_t t,mach_port_name_t n,mach_msg_header_t *rm,mach_msg_size_t limit){unsigned i=enter(2,m,o,s,r,__builtin_return_address(0));mach_msg_return_t k=mach_msg_overwrite(m,o,s,r,p,t,n,rm,limit);leave(i,rm?rm:m,o,rm?limit:r,k);return k;}
// Source-authoritative ABI: Apple xnu-12377.121.6 osfmk/mach/message.h:1373.
// Same version as running kernel; native binding and LLVM are in abi-proof.json.
// No guessed callable private ABI; original arguments and result are unchanged.
extern mach_msg_return_t mach_msg2_internal(void*,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t);
struct OwnedMachVector { uint64_t data,receive;uint32_t send_size,receive_size; };
_Static_assert(sizeof(struct OwnedMachVector)==24,"exact matching XNU vector layout");
static struct OwnedRight sample_send_once(mach_port_name_t name){
 struct OwnedRight s={0};mach_port_type_t type=0;mach_port_urefs_t refs=0;
 s.type_status=mach_port_type(mach_task_self(),name,&type);s.type=type;
 s.refs_status=mach_port_get_refs(mach_task_self(),name,MACH_PORT_RIGHT_SEND_ONCE,&refs);s.refs=refs;return s;
}
static mach_msg_return_t traced_msg2(void *data,uint64_t opt,uint64_t bits_size,uint64_t ports,uint64_t voucher_id,uint64_t desc_recv,uint64_t recv_priority,uint64_t timeout){
 if(!atomic_load(&active))return mach_msg2_internal(data,opt,bits_size,ports,voucher_id,desc_recv,recv_priority,timeout);
 mach_msg_header_t *send=data,*receive=data;uint32_t ss=(uint32_t)(bits_size>>32),rs=(uint32_t)recv_priority;
 if(data&&(opt&UINT64_C(0x100000000))){struct OwnedMachVector*v=data;send=(void*)(uintptr_t)v[0].data;receive=(void*)(uintptr_t)(v[0].receive?v[0].receive:v[0].data);ss=v[0].send_size;rs=v[0].receive_size;}
 unsigned i=enter(3,send,(uint32_t)opt,ss,rs,__builtin_return_address(0));if(i<LIMIT)rows[i].options64=opt;if((opt&MACH_SEND_MSG)&&send&&ss>=sizeof(*send)&&send->msgh_id==0x10000000){const char needle[]="sceneID:sendActions:toExtension:completion:";size_t length=ss-sizeof(*send);if(length<=4096&&memmem((unsigned char*)send+sizeof(*send),length,needle,sizeof(needle)-1)){atomic_store(&header_reply_port,send->msgh_local_port);atomic_store(&reply_bits,(uint32_t)bits_size);atomic_store_explicit(&reply_port,(uint32_t)(ports>>32),memory_order_release);}}
 int selected=i<LIMIT && atomic_load_explicit(&reply_port,memory_order_acquire) && (opt&MACH_SEND_MSG) && send && ss==sizeof(*send)+20 && send->msgh_id==0x20000000 && !memcmp((unsigned char*)send+sizeof(*send),"CPX@",4);
 if(selected){rows[i].reply_selected=1;rows[i].reply_remote_name=(uint32_t)ports;rows[i].reply_header_remote_name=send->msgh_remote_port;rows[i].reply_receive_name=atomic_load(&reply_port);rows[i].reply_disposition=(uint32_t)bits_size&255;rows[i].reply_before=sample_send_once((uint32_t)ports);}
 mach_msg_return_t result=mach_msg2_internal(data,opt,bits_size,ports,voucher_id,desc_recv,recv_priority,timeout);
 if(selected)rows[i].reply_after=sample_send_once(rows[i].reply_remote_name);
 leave(i,receive,(uint32_t)opt,rs,result);return result;
}
static _Atomic unsigned abandon_active,release_count,release_calls,release_window;
static _Thread_local unsigned release_depth,abandon_owned_thread;
static struct ReleaseRow releases[16];static _Atomic unsigned release_done[16];static dispatch_semaphore_t late_event;
void trace_abandon_begin(void){atomic_store(&release_window,2);abandon_owned_thread=1;atomic_store(&abandon_active,1);}
void trace_late_begin(void){late_event=dispatch_semaphore_create(0);atomic_store(&release_window,1);abandon_owned_thread=1;atomic_store(&abandon_active,1);}
unsigned trace_late_wait(void){return (unsigned)dispatch_semaphore_wait(late_event,dispatch_time(DISPATCH_TIME_NOW,500*NSEC_PER_MSEC));}
unsigned trace_release_calls(void){return atomic_load(&release_calls);}
void trace_abandon_end(void){atomic_store(&abandon_active,0);abandon_owned_thread=0;}
unsigned trace_release_rows(struct ReleaseRow*out,unsigned cap,unsigned*calls){unsigned n=atomic_load(&release_count);if(n>16)n=16;if(n>cap)n=cap;for(unsigned i=0;i<n;i++){unsigned complete=atomic_load_explicit(&release_done[i],memory_order_acquire);if(complete)out[i]=releases[i];else memset(&out[i],0,sizeof(out[i]));out[i].complete=complete;}*calls=atomic_load(&release_calls);return n;}
static unsigned release_enter(ipc_space_t task,mach_port_name_t name,unsigned api,void *caller){
 if(release_depth++||!atomic_load(&abandon_active)||task!=mach_task_self())return 16;
 atomic_fetch_add(&release_calls,1);struct OwnedRight before=sample_send_once(name);
 if(before.type_status||(before.type!=MACH_PORT_TYPE_SEND_ONCE&&before.type!=MACH_PORT_TYPE_DEAD_NAME))return 16;
 unsigned i=atomic_fetch_add(&release_count,1);if(i<16)releases[i]=(struct ReleaseRow){.caller=(uintptr_t)caller,.window=atomic_load(&release_window),.api=api,.name=name,.receive_name=atomic_load(&reply_port),.before=before};if(i<16)releases[i].dead_before_status=mach_port_get_refs(mach_task_self(),name,MACH_PORT_RIGHT_DEAD_NAME,&releases[i].dead_before_refs);return i;
}
static void release_leave(unsigned i,kern_return_t k){if(i<16){releases[i].result=k;releases[i].after=sample_send_once(releases[i].name);releases[i].dead_after_status=mach_port_get_refs(mach_task_self(),releases[i].name,MACH_PORT_RIGHT_DEAD_NAME,&releases[i].dead_after_refs);atomic_store_explicit(&release_done[i],1,memory_order_release);if(releases[i].window==1&&releases[i].before.type==MACH_PORT_TYPE_DEAD_NAME)dispatch_semaphore_signal(late_event);}release_depth--;}
static kern_return_t traced_deallocate(ipc_space_t task,mach_port_name_t name){if(!atomic_load(&abandon_active)||(atomic_load(&release_window)!=1&&!abandon_owned_thread))return mach_port_deallocate(task,name);unsigned i=release_enter(task,name,1,__builtin_return_address(0));kern_return_t k=mach_port_deallocate(task,name);release_leave(i,k);return k;}
static kern_return_t traced_mod_refs(ipc_space_t task,mach_port_name_t name,mach_port_right_t right,mach_port_delta_t delta){if(!atomic_load(&abandon_active)||(atomic_load(&release_window)!=1&&!abandon_owned_thread))return mach_port_mod_refs(task,name,right,delta);unsigned i=release_enter(task,name,2,__builtin_return_address(0));kern_return_t k=mach_port_mod_refs(task,name,right,delta);release_leave(i,k);return k;}
static void traced_destroy(mach_msg_header_t *message){
 if(!atomic_load(&abandon_active)||atomic_load(&release_window)!=1||!message||message->msgh_id!=0x20000000){mach_msg_destroy(message);return;}
 unsigned i=release_enter(mach_task_self(),message->msgh_remote_port,3,__builtin_return_address(0));
 if(i<16){releases[i].message_id=message->msgh_id;releases[i].message_bits=message->msgh_bits;releases[i].message_size=message->msgh_size;if(message->msgh_size==sizeof(*message)+20){releases[i].body_size=20;memcpy(releases[i].body,(unsigned char*)message+sizeof(*message),20);}}
 mach_msg_destroy(message);release_leave(i,0);
}
__attribute__((used)) static struct { const void *replacement,*replacee; } interpose[] __attribute__((section("__DATA,__interpose")))={{(const void*)traced_destroy,(const void*)mach_msg_destroy},{(const void*)traced_deallocate,(const void*)mach_port_deallocate},{(const void*)traced_mod_refs,(const void*)mach_port_mod_refs},{(const void*)traced_msg2,(const void*)mach_msg2_internal},{(const void*)traced_msg,(const void*)mach_msg},{(const void*)traced_overwrite,(const void*)mach_msg_overwrite}};
void trace_begin(void){atomic_store(&count,0);for(unsigned i=0;i<LIMIT;i++)atomic_store(&done[i],0);atomic_store(&active,1);}
unsigned trace_end(struct TraceRow *out,unsigned cap){atomic_store(&active,0);unsigned n=atomic_load(&count);if(n>LIMIT)n=LIMIT;if(n>cap)n=cap;for(unsigned i=0;i<n;i++){unsigned complete=atomic_load_explicit(&done[i],memory_order_acquire);if(complete)out[i]=rows[i];else memset(&out[i],0,sizeof(out[i]));out[i].complete=complete;}return n;}

mach_port_name_t trace_owned_reply_port(void){return atomic_load_explicit(&reply_port,memory_order_acquire);}
mach_port_name_t trace_header_reply_port(void){return atomic_load(&header_reply_port);}
uint32_t trace_owned_reply_bits(void){return atomic_load(&reply_bits);}
