#include <mach/mach.h>
int peer_setup(int argc,char **argv);
void peer_finish(void);
void trace_route(mach_port_t target,int export_endpoint);
void peer_wait_for_exit(void);
int peer_is_reaped(void);
