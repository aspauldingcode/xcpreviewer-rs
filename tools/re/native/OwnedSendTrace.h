#include <stdint.h>
struct OwnedSendRow {uint32_t api,phase,options,send_size,bits,remote,packed_remote,id,marker,complete;int32_t result,before_type_result,before_refs_result,after_type_result;uint32_t before_type,before_refs,after_type,queried;uintptr_t message,caller;};
void owned_send_trace_begin(void);
void owned_send_trace_phase(unsigned);
unsigned owned_send_trace_end(struct OwnedSendRow*,unsigned);
const void *owned_send_trace_original_mach2(void);

unsigned owned_send_trace_total(void);
