#include <stdint.h>
#include <mach/mach.h>
struct TraceRow { uint32_t api,options,send_size,receive_size,send_bits,send_id,receive_bits,receive_id; int32_t result; uint32_t complete,receive_message_size,send_body_size,receive_body_size; uintptr_t caller; unsigned char send_body[4096],receive_body[4096]; };
void trace_begin(void);
unsigned trace_end(struct TraceRow *rows,unsigned capacity);
