#include <stdint.h>
void * _Nullable owned_swift_call(void * _Nonnull function, const void * _Nullable arg0, const void * _Nullable arg1, const void * _Nullable context, void * _Nullable result);
uintptr_t owned_symbol_offset(void * _Nonnull symbol);
const char * _Nonnull owned_symbol_path(void * _Nonnull symbol);

unsigned long owned_swift_scalar(void *function, const void *arg0, const void *arg1, const void *arg2, const void *arg3, const void *context);
unsigned owned_image_count(void);
const char *owned_image_path(unsigned index);
const unsigned char *owned_image_uuid(unsigned index);

void *owned_swift_call3(void *function,const void *arg0,const void *arg1,const void *arg2,const void *context,void *result);

void owned_transport_witness(void);

void owned_reply_unit(void *function,const void *context);

void *owned_exchange_uv(const void *request,const void *response,void **receipt);
void owned_make_handler(void *function,const void *callsite,const void *self,void *pair);
void owned_callsite_init(void *function,void *result);

void owned_receiver_adapter(void);
void owned_encoded_adapter(void);
void owned_receive_oneway(void *function,const void *uv,const void *metadata,const void *self);
void owned_receive_reply(void *function,const void *uv,const void *handler,const void *handlerContext,const void *metadata,const void *self);
void *owned_uv_summary(const void *uv);
