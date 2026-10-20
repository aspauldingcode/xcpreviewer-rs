#include <xpc/xpc.h>
#include <dlfcn.h>
#include <mach-o/loader.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
int main(void){Dl_info d={0};void *p=(void*)xpc_connection_send_message;if(!dladdr(p,&d)||strcmp(d.dli_fname,"/usr/lib/system/libxpc.dylib"))return 2;const struct mach_header_64*h=d.dli_fbase;if(h->magic!=MH_MAGIC_64)return 3;const struct load_command*l=(void*)(h+1);unsigned char expected[16]={0xc4,0x0f,0xca,0xe8,0x7a,0x17,0x3d,0x82,0x87,0xcb,0x3d,0xa4,0x80,0x2a,0xde,0xf1};int found=0;for(unsigned i=0;i<h->ncmds;i++){if(l->cmd==LC_UUID){const struct uuid_command*u=(void*)l;if(memcmp(u->uuid,expected,16))return 4;found=1;}l=(void*)((char*)l+l->cmdsize);}if(!found)return 5;printf("{\"uuid\":\"c40fcae87a173d8287cb3da4802adef1\",\"offset\":%llu,\"prefix32_hex\":\"",(unsigned long long)((uintptr_t)p-(uintptr_t)d.dli_fbase));for(unsigned i=0;i<32;i++)printf("%02x",((unsigned char*)p)[i]);puts("\"}");return 0;}
