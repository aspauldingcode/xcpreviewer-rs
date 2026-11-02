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

#import <Foundation/Foundation.h>
void *owned_create_client(void);
void *owned_uv_create(NSDictionary *d);
NSDictionary *owned_uv_dictionary(const void *p);
void owned_obj_release(const void *p);
NSDictionary *owned_peer_result(void);
void owned_peer_close(void);
void owned_service_reply(void);

unsigned long owned_object_size(const void *p);
void *owned_seed_client(void);
void owned_seed_close(void);

NSData *owned_uv_data(const void *p);
