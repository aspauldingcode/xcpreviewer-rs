#define main surface_success_main
#include "surface_ipc_probe.c"
#undef main
static int removed(mach_port_t p){mach_port_type_t t=0;return mach_port_type(mach_task_self(),p,&t)==KERN_INVALID_NAME;}
static int sample(IOSurfaceRef *refs,unsigned n,unsigned stage,const char *folder){
 printf("%s{\"stage\":%u,\"local\":[",stage?",":"",stage);for(unsigned i=0;i<n;i++)printf("%s%d",i?",":"",IOSurfaceGetUseCount(refs[i]));printf("],\"global\":[");for(unsigned i=0;i<n;i++)printf("%s%d",i?",":"",!!IOSurfaceIsInUse(refs[i]));printf("]}");
 for(unsigned i=0;i<n;i++){uint8_t bytes[LIMIT];size_t count=IOSurfaceGetAllocSize(refs[i]);char name[64];snprintf(name,sizeof(name),"stage-%u-alias-%u.bin",stage,i);if(count!=16384 || IOSurfaceGetWidth(refs[i])!=17 || IOSurfaceGetHeight(refs[i])!=9 || IOSurfaceGetBytesPerRow(refs[i])!=128 || !snapshot(refs[i],bytes,count) || !write_bytes(folder,name,bytes,count))return 0;}return 1;
}
int main(int argc,char **argv){
 alarm(10);if(argc!=2)return 2;IOSurfaceRef original=NULL,a=NULL,b=NULL,lookup=NULL;mach_port_t port=MACH_PORT_NULL;int result=3,contributions=0;uint32_t id=0;
 original=create_surface(17,9,49,NULL);if(!original)goto done;id=IOSurfaceGetID(original);port=IOSurfaceCreateMachPort(original);if(!MACH_PORT_VALID(port) || !send_refs(port,1))goto done;a=IOSurfaceLookupFromMachPort(port);b=IOSurfaceLookup(id);if(!a || !b || IOSurfaceGetID(a)!=id || IOSurfaceGetID(b)!=id)goto done;
 int oa=original==a,ob=original==b,ab=a==b;mach_port_t retired=port;if(mach_port_deallocate(mach_task_self(),port) || !removed(retired))goto done;port=MACH_PORT_NULL;
 printf("{\"pid\":%d,\"surface_id\":%u,\"allocation_bytes\":16384,\"stride\":128,\"resource_name_removed\":true,\"equal_refs\":[%s,%s,%s],\"samples\":[",getpid(),id,oa?"true":"false",ob?"true":"false",ab?"true":"false");
 IOSurfaceRef three[3]={original,a,b};if(!sample(three,3,0,argv[1]))goto done;
 IOSurfaceIncrementUseCount(a);contributions++;if(!sample(three,3,1,argv[1]))goto done;
 IOSurfaceIncrementUseCount(b);contributions++;if(!sample(three,3,2,argv[1]))goto done;
 IOSurfaceDecrementUseCount(original);contributions--;if(!sample(three,3,3,argv[1]))goto done;
 CFRelease(a);a=NULL;IOSurfaceRef two[2]={original,b};if(!sample(two,2,4,argv[1]))goto done;
 IOSurfaceDecrementUseCount(b);contributions--;if(!sample(two,2,5,argv[1]))goto done;
 CFRelease(original);original=NULL;IOSurfaceRef one[1]={b};if(!sample(one,1,6,argv[1]))goto done;
 CFRelease(b);b=NULL;usleep(100000);lookup=IOSurfaceLookup(id);int present=lookup!=NULL;if(lookup){CFRelease(lookup);lookup=NULL;}printf("],\"all_cf_owners_released\":true,\"balanced_use_calls\":true,\"lookup_after_release\":%s}\n",present?"true":"false");result=0;
 done:if(contributions){IOSurfaceRef keeper=original?original:(a?a:b);if(keeper)while(contributions-->0)IOSurfaceDecrementUseCount(keeper);}if(lookup)CFRelease(lookup);if(a)CFRelease(a);if(b)CFRelease(b);if(original)CFRelease(original);if(MACH_PORT_VALID(port))mach_port_deallocate(mach_task_self(),port);return result;
}
