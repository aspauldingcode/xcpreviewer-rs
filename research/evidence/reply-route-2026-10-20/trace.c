#include "trace.h"
#include <stdatomic.h>
#include <string.h>
#define LIMIT 256
static _Atomic unsigned active,count;
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
 if(i<LIMIT){rows[i].result=result;if(result==MACH_RCV_TOO_LARGE&&(opt&MACH_RCV_LARGE)&&recv&&cap>=sizeof(*recv))rows[i].receive_message_size=recv->msgh_size;if(result==MACH_MSG_SUCCESS&&(opt&MACH_RCV_MSG)&&recv&&cap>=sizeof(*recv)){rows[i].receive_bits=recv->msgh_bits;rows[i].receive_id=recv->msgh_id;rows[i].receive_message_size=recv->msgh_size;if(recv->msgh_size>=sizeof(*recv)&&recv->msgh_size<=cap){rows[i].receive_body_size=recv->msgh_size-sizeof(*recv);if(rows[i].receive_body_size>4096)rows[i].receive_body_size=4096;memcpy(rows[i].receive_body,(unsigned char*)recv+sizeof(*recv),rows[i].receive_body_size);}}atomic_store_explicit(&done[i],1,memory_order_release);}depth--;
}
static mach_msg_return_t traced_msg(mach_msg_header_t *m,mach_msg_option_t o,mach_msg_size_t s,mach_msg_size_t r,mach_port_name_t p,mach_msg_timeout_t t,mach_port_name_t n){unsigned i=enter(1,m,o,s,r,__builtin_return_address(0));mach_msg_return_t k=mach_msg(m,o,s,r,p,t,n);leave(i,m,o,r,k);return k;}
static mach_msg_return_t traced_overwrite(mach_msg_header_t *m,mach_msg_option_t o,mach_msg_size_t s,mach_msg_size_t r,mach_port_name_t p,mach_msg_timeout_t t,mach_port_name_t n,mach_msg_header_t *rm,mach_msg_size_t limit){unsigned i=enter(2,m,o,s,r,__builtin_return_address(0));mach_msg_return_t k=mach_msg_overwrite(m,o,s,r,p,t,n,rm,limit);leave(i,rm?rm:m,o,rm?limit:r,k);return k;}
__attribute__((used)) static struct { const void *replacement,*replacee; } interpose[] __attribute__((section("__DATA,__interpose")))={{(const void*)traced_msg,(const void*)mach_msg},{(const void*)traced_overwrite,(const void*)mach_msg_overwrite}};
void trace_begin(void){atomic_store(&count,0);for(unsigned i=0;i<LIMIT;i++)atomic_store(&done[i],0);atomic_store(&active,1);}
unsigned trace_end(struct TraceRow *out,unsigned cap){atomic_store(&active,0);unsigned n=atomic_load(&count);if(n>LIMIT)n=LIMIT;if(n>cap)n=cap;for(unsigned i=0;i<n;i++){unsigned complete=atomic_load_explicit(&done[i],memory_order_acquire);if(complete)out[i]=rows[i];else memset(&out[i],0,sizeof(out[i]));out[i].complete=complete;}return n;}
