#define main surface_success_main
#include "surface_ipc_probe.c"
#undef main

static int gone(mach_port_t port) { mach_port_type_t type=0;return mach_port_type(mach_task_self(),port,&type)==KERN_INVALID_NAME; }
static int capture(IOSurfaceRef s,const char *folder,const char *name) {
    size_t count=IOSurfaceGetAllocSize(s);uint8_t bytes[LIMIT];
    return count && count<=LIMIT && snapshot(s,bytes,count) && write_bytes(folder,name,bytes,count);
}
int main(int argc,char **argv) {
    alarm(12);if(argc!=3 || (strcmp(argv[1],"released") && strcmp(argv[1],"held")))return 2;
    int held=!strcmp(argv[1],"held"),result=3,matched=0,before_present=0,port_released=0;const char *folder=argv[2];
    IOSurfaceRef first=NULL,candidate=NULL,lookup=NULL;mach_port_t port=MACH_PORT_NULL;uint32_t old_id=0,observed[64]={0};unsigned attempts=0;size_t stride=0,count=0;
    first=create_surface(17,9,49,NULL);if(!first)goto done;stride=IOSurfaceGetBytesPerRow(first);count=IOSurfaceGetAllocSize(first);old_id=IOSurfaceGetID(first);
    if(!count || count>LIMIT || !capture(first,folder,"initial.bin"))goto done;
    port=IOSurfaceCreateMachPort(first);if(!MACH_PORT_VALID(port) || !send_refs(port,1))goto done;
    CFRelease(first);first=NULL;
    if(!held){if(mach_port_deallocate(mach_task_self(),port) || !gone(port))goto done;port_released=1;}
    usleep(100000);lookup=IOSurfaceLookup(old_id);before_present=lookup!=NULL;
    if(lookup){if(IOSurfaceGetID(lookup)!=old_id || !capture(lookup,folder,"lookup-before.bin"))goto done;CFRelease(lookup);lookup=NULL;}
    for(unsigned index=0;index<64;index++) {
        candidate=create_surface(17,9,50,NULL);if(!candidate || IOSurfaceGetBytesPerRow(candidate)!=stride || IOSurfaceGetAllocSize(candidate)!=count)goto done;
        uint32_t id=IOSurfaceGetID(candidate);observed[attempts++]=id;char name[64];snprintf(name,sizeof(name),"candidate-%03u.bin",index);
        if(!capture(candidate,folder,name))goto done;
        if(id==old_id){matched=1;lookup=IOSurfaceLookup(old_id);if(!lookup || IOSurfaceGetID(lookup)!=id || !capture(lookup,folder,"stale-lookup.bin"))goto done;CFRelease(lookup);lookup=NULL;break;}
        CFRelease(candidate);candidate=NULL;
    }
    if(held){
        if(matched || !send_refs(port,1))goto done;lookup=IOSurfaceLookup(old_id);
        if(!lookup || IOSurfaceGetID(lookup)!=old_id || !capture(lookup,folder,"retained-lookup.bin"))goto done;CFRelease(lookup);lookup=NULL;
        if(mach_port_deallocate(mach_task_self(),port) || !gone(port))goto done;port_released=1;
    }
    if(candidate){CFRelease(candidate);candidate=NULL;}
    port=MACH_PORT_NULL;usleep(100000);lookup=IOSurfaceLookup(old_id);int settled_present=lookup!=NULL;
    if(lookup){if(!capture(lookup,folder,"settled-lookup.bin"))goto done;CFRelease(lookup);lookup=NULL;}
    printf("{\"mode\":\"%s\",\"pid\":%d,\"old_id\":%u,\"stride\":%zu,\"allocation_bytes\":%zu,\"owner_cf_released\":true,\"right_held_during_churn\":%s,\"right_refs_during_churn\":%d,\"before_lookup_present\":%s,\"attempts\":%u,\"matched\":%s,\"port_released\":%s,\"settled_lookup_present\":%s,\"candidate_ids\":[",argv[1],(int)getpid(),old_id,stride,count,held?"true":"false",held?1:0,before_present?"true":"false",attempts,matched?"true":"false",port_released?"true":"false",settled_present?"true":"false");
    for(unsigned i=0;i<attempts;i++)printf("%s%u",i?",":"",observed[i]);printf("]}\n");result=0;
 done:
    if(lookup)CFRelease(lookup);if(candidate)CFRelease(candidate);if(first)CFRelease(first);
    if(MACH_PORT_VALID(port) && !port_released)mach_port_deallocate(mach_task_self(),port);return result;
}
