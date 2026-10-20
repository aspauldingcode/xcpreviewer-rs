#include <xpc/xpc.h>
#include <dlfcn.h>
#include <mach-o/loader.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
int main(int argc,char**argv){if(argc!=2)return 6;Dl_info d={0};void *p=(void*)xpc_connection_send_message;if(!dladdr(p,&d)||strcmp(d.dli_fname,"/usr/lib/system/libxpc.dylib"))return 2;const struct mach_header_64*h=d.dli_fbase;if(h->magic!=MH_MAGIC_64)return 3;const struct load_command*l=(void*)(h+1);unsigned char expected[16]={0xc4,0x0f,0xca,0xe8,0x7a,0x17,0x3d,0x82,0x87,0xcb,0x3d,0xa4,0x80,0x2a,0xde,0xf1};int found=0;for(unsigned i=0;i<h->ncmds;i++){if(l->cmd==LC_UUID){const struct uuid_command*u=(void*)l;if(memcmp(u->uuid,expected,16))return 4;found=1;}l=(void*)((char*)l+l->cmdsize);}if(!found)return 5;const unsigned offsets[]={24536,49728,49220,54636,54884};const unsigned sizes[]={124,540,204,248,296};for(unsigned i=0;i<5;i++){if(offsets[i]+sizes[i]>345440)return 7;char name[1024];if(snprintf(name,sizeof(name),"%s/%u.bin",argv[1],offsets[i])>=(int)sizeof(name))return 8;FILE*f=fopen(name,"wb");if(!f)return 9;if(fwrite((char*)d.dli_fbase+offsets[i],1,sizes[i],f)!=sizes[i])return 10;fclose(f);}return 0;}
