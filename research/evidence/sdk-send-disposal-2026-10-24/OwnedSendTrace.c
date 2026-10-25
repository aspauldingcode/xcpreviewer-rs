#include "OwnedSendTrace.h"
#include <mach/mach.h>
#include <stdatomic.h>
#include <string.h>
#define LIMIT 512
// Exact recovered declaration: Apple xnu-12377.121.6/osfmk/mach/message.h:1373.
// Matching libsyscall/mach/mach_msg.c:86 and pinned native image verify authority.
// https://raw.githubusercontent.com/apple-oss-distributions/xnu/xnu-12377.121.6/osfmk/mach/message.h
extern mach_msg_return_t mach_msg2_internal(void*,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t);
struct Vector {uint64_t data,receive;uint32_t send_size,receive_size;};
_Static_assert(sizeof(struct Vector)==24,"matching source-authoritative Mach2 vector");
static struct OwnedSendRow rows[LIMIT];static _Atomic unsigned active,count,phase,done[LIMIT];static _Thread_local unsigned depth;
static unsigned marker(const void *data,unsigned bytes){static const char text[]="owned reply marker";if(bytes>65536)return 0;const unsigned char *p=data;for(unsigned i=0;i+sizeof(text)-1<=bytes;i++)if(!memcmp(p+i,text,sizeof(text)-1))return 1;return 0;}
static unsigned enter(unsigned api,mach_msg_header_t *m,unsigned opt,unsigned size,unsigned packed){
 if(depth++||!atomic_load(&active))return LIMIT;unsigned i=atomic_fetch_add(&count,1);if(i>=LIMIT)return LIMIT;
 rows[i]=(struct OwnedSendRow){.api=api,.phase=atomic_load(&phase),.options=opt,.send_size=size,.packed_remote=packed,.message=(uintptr_t)m};
 if(m&&size>=sizeof(*m)){rows[i].bits=m->msgh_bits;rows[i].remote=m->msgh_remote_port;rows[i].id=(uint32_t)m->msgh_id;rows[i].marker=marker(m,size);}return i;
}
static void leave(unsigned i,mach_msg_return_t result){if(i<LIMIT){rows[i].result=result;atomic_store_explicit(&done[i],1,memory_order_release);}depth--;}
static mach_msg_return_t observe_msg(mach_msg_header_t*m,mach_msg_option_t o,mach_msg_size_t s,mach_msg_size_t r,mach_port_name_t p,mach_msg_timeout_t t,mach_port_name_t n){unsigned i=enter(1,(o&MACH_SEND_MSG)?m:NULL,o,(o&MACH_SEND_MSG)?s:0,0);if(i<LIMIT)rows[i].caller=(uintptr_t)__builtin_return_address(0);mach_msg_return_t result=mach_msg(m,o,s,r,p,t,n);leave(i,result);return result;}
static mach_msg_return_t observe_msg2(void*d,uint64_t o,uint64_t bs,uint64_t ports,uint64_t vi,uint64_t dr,uint64_t rp,uint64_t t){mach_msg_header_t*m=d;unsigned s=(unsigned)(bs>>32);if(d&&(o&UINT64_C(0x100000000))){const struct Vector*v=d;m=(void*)(uintptr_t)v[0].data;s=v[0].send_size;}unsigned i=enter(2,(o&MACH_SEND_MSG)?m:NULL,(unsigned)o,(o&MACH_SEND_MSG)?s:0,(unsigned)ports);if(i<LIMIT)rows[i].caller=(uintptr_t)__builtin_return_address(0);mach_msg_return_t result=mach_msg2_internal(d,o,bs,ports,vi,dr,rp,t);leave(i,result);return result;}
static void observe_destroy(mach_msg_header_t*m){unsigned i=enter(3,m,0,m?m->msgh_size:0,0);mach_port_t name=MACH_PORT_NULL;if(i<LIMIT)rows[i].caller=(uintptr_t)__builtin_return_address(0);
 if(i<LIMIT&&m&&MACH_MSGH_BITS_REMOTE(m->msgh_bits)==MACH_MSG_TYPE_MOVE_SEND_ONCE&&MACH_PORT_VALID(m->msgh_remote_port)){
  name=m->msgh_remote_port;rows[i].queried=1;mach_port_type_t type=0;rows[i].before_type_result=mach_port_type(mach_task_self(),name,&type);rows[i].before_type=type;mach_port_urefs_t refs=0;
  if(rows[i].before_type_result==KERN_SUCCESS&&(type&MACH_PORT_TYPE_DEAD_NAME)){rows[i].before_refs_result=mach_port_get_refs(mach_task_self(),name,MACH_PORT_RIGHT_DEAD_NAME,&refs);rows[i].before_refs=refs;}else rows[i].before_refs_result=-1;
 }
 mach_msg_destroy(m);
 if(i<LIMIT&&MACH_PORT_VALID(name)){mach_port_type_t type=0;rows[i].after_type_result=mach_port_type(mach_task_self(),name,&type);rows[i].after_type=type;}
 leave(i,0);
}
__attribute__((used))static struct{const void*replacement,*original;} interpose[] __attribute__((section("__DATA,__interpose")))={{(const void*)observe_msg,(const void*)mach_msg},{(const void*)observe_msg2,(const void*)mach_msg2_internal},{(const void*)observe_destroy,(const void*)mach_msg_destroy}};
void owned_send_trace_begin(void){atomic_store(&count,0);atomic_store(&phase,0);for(unsigned i=0;i<LIMIT;i++)atomic_store(&done[i],0);atomic_store(&active,1);}
void owned_send_trace_phase(unsigned p){atomic_store(&phase,p);}
unsigned owned_send_trace_end(struct OwnedSendRow*out,unsigned cap){atomic_store(&active,0);unsigned n=atomic_load(&count);if(n>LIMIT)n=LIMIT;if(n>cap)n=cap;for(unsigned i=0;i<n;i++){unsigned finished=atomic_load_explicit(&done[i],memory_order_acquire);if(finished)out[i]=rows[i];else memset(&out[i],0,sizeof(out[i]));out[i].complete=finished;}return n;}
const void*owned_send_trace_original_mach2(void){return (const void*)mach_msg2_internal;}

unsigned owned_send_trace_total(void){return atomic_load(&count);}
