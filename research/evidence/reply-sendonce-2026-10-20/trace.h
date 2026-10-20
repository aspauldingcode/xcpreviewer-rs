#include <stdint.h>
#include <mach/mach.h>
struct OwnedRight { int32_t type_status,refs_status; uint32_t type,refs; };
struct TraceRow { uint32_t reply_selected,reply_remote_name,reply_header_remote_name,reply_receive_name,reply_disposition; struct OwnedRight reply_before,reply_after; uint32_t api,options,send_size,receive_size,send_bits,send_id,receive_bits,receive_id; int32_t result; uint32_t complete,receive_message_size,send_body_size,receive_body_size; uintptr_t caller; uint64_t options64; uint32_t receive_audit_pid; unsigned char send_body[4096],receive_body[4096]; };
void trace_begin(void);
unsigned trace_end(struct TraceRow *rows,unsigned capacity);

int trace_set_replacement(const unsigned char *bytes,unsigned count);

int trace_set_descriptor_order(const uint32_t *order,unsigned count);

mach_port_name_t trace_owned_reply_port(void);
mach_port_name_t trace_header_reply_port(void);
uint32_t trace_owned_reply_bits(void);

struct ReleaseRow { uint32_t api,name,receive_name; int32_t result; struct OwnedRight before,after; };
void trace_abandon_begin(void);
void trace_abandon_end(void);
unsigned trace_release_rows(struct ReleaseRow *out,unsigned cap,unsigned *calls);
