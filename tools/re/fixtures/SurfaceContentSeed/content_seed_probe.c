#define main surface_success_main
#include "surface_ipc_probe.c"
#undef main
static int capture_pair(IOSurfaceRef s,IOSurfaceRef a,unsigned stage,const char *folder){
 IOSurfaceRef refs[2]={s,a};for(unsigned i=0;i<2;i++){uint8_t bytes[LIMIT];char name[64];snprintf(name,sizeof(name),"stage-%u-alias-%u.bin",stage,i);if(IOSurfaceGetAllocSize(refs[i])!=16384 || !snapshot(refs[i],bytes,16384) || !write_bytes(folder,name,bytes,16384))return 0;}return 1;
}
int main(int argc,char **argv){
 alarm(10);if(argc!=2)return 2;IOSurfaceRef s=create_surface(17,9,49,NULL),a=NULL;mach_port_t port=MACH_PORT_NULL;int result=3;uint32_t id=0;if(!s)goto done;
 if(IOSurfaceGetBytesPerRow(s)!=128 || IOSurfaceGetAllocSize(s)!=16384)goto done;id=IOSurfaceGetID(s);port=IOSurfaceCreateMachPort(s);if(!MACH_PORT_VALID(port) || !send_refs(port,1))goto done;a=IOSurfaceLookupFromMachPort(port);if(!a || IOSurfaceGetID(a)!=id)goto done;mach_port_t old=port;if(mach_port_deallocate(mach_task_self(),port))goto done;mach_port_type_t type=0;if(mach_port_type(mach_task_self(),old,&type)!=KERN_INVALID_NAME)goto done;port=MACH_PORT_NULL;
 uint32_t initial=IOSurfaceGetSeed(s);if(!capture_pair(s,a,0,argv[1]))goto done;
 printf("{\"pid\":%d,\"surface_id\":%u,\"stride\":128,\"allocation_bytes\":16384,\"resource_name_removed\":true,\"distinct_alias\":%s,\"initial_seed\":%u,\"initial_alias_seed\":%u,\"steps\":[",getpid(),id,s!=a?"true":"false",initial,IOSurfaceGetSeed(a));
 const char *names[]={"read-only","write-noop","active","padding","tail","restore"};
 for(unsigned i=0;i<6;i++){
  uint32_t before=IOSurfaceGetSeed(s),locked=0,unlocked=0;IOSurfaceLockOptions options=i==0?kIOSurfaceLockReadOnly:0;IOSurfaceRef writer=(i&1)?a:s;
  kern_return_t l=IOSurfaceLock(writer,options,&locked);if(l)goto done;uint8_t *bytes=IOSurfaceGetBaseAddress(writer);
  if(i==2)bytes[0]^=1;if(i==3)bytes[68]^=1;if(i==4)bytes[16383]^=1;if(i==5){bytes[0]^=1;bytes[68]^=1;bytes[16383]^=1;}
  kern_return_t u=IOSurfaceUnlock(writer,options,&unlocked);if(u)goto done;uint32_t after=IOSurfaceGetSeed(s),alias=IOSurfaceGetSeed(a);if(!capture_pair(s,a,i+1,argv[1]))goto done;
  printf("%s{\"name\":\"%s\",\"writer_alias\":%u,\"before\":%u,\"lock_seed\":%u,\"unlock_seed\":%u,\"after\":%u,\"alias_after\":%u,\"after_snapshots\":%u,\"surface_id\":%u,\"lock_code\":%d,\"unlock_code\":%d}",i?",":"",names[i],i&1,before,locked,unlocked,after,alias,IOSurfaceGetSeed(s),IOSurfaceGetID(s),l,u);
 }
 CFRelease(a);a=NULL;CFRelease(s);s=NULL;usleep(100000);IOSurfaceRef last=IOSurfaceLookup(id);int present=last!=NULL;if(last)CFRelease(last);printf("],\"all_cf_owners_released\":true,\"lookup_after_release\":%s}\n",present?"true":"false");result=0;
 done:if(a)CFRelease(a);if(s)CFRelease(s);if(MACH_PORT_VALID(port))mach_port_deallocate(mach_task_self(),port);return result;
}
