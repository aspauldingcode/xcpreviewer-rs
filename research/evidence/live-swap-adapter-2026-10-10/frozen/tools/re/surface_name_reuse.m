// Owned public-API control: bounded task-local send-name churn.
#import <Foundation/Foundation.h>
#import <IOSurface/IOSurface.h>
#import <mach/mach.h>
static NSData *fill(IOSurfaceRef s,unsigned seed) {
    size_t n=IOSurfaceGetAllocSize(s),stride=IOSurfaceGetBytesPerRow(s);
    if(IOSurfaceLock(s,0,NULL))return nil;
    uint8_t *b=IOSurfaceGetBaseAddress(s);memset(b,0xa5,n);
    for(size_t y=0;y<IOSurfaceGetHeight(s);y++)for(size_t x=0;x<IOSurfaceGetWidth(s);x++)for(size_t c=0;c<4;c++)
        b[y*stride+x*4+c]=c==3?255:(seed+x*17+y*31+c*53)&255;
    NSData *d=[NSData dataWithBytes:b length:n];if(IOSurfaceUnlock(s,0,NULL))return nil;return d;
}
static unsigned lookup(mach_port_t p) {IOSurfaceRef s=IOSurfaceLookupFromMachPort(p);if(!s)return 0;unsigned v=IOSurfaceGetID(s);CFRelease(s);return v;}
int main(int argc,const char **argv) {@autoreleasepool {
    if(argc!=4 && argc!=5)return 2;
    BOOL retained=argc==5 && strcmp(argv[4],"retained")==0;if(argc==5 && !retained)return 2;
    for(int i=1;i<4;i++)if(!argv[i][0]||strlen(argv[i])>3||strspn(argv[i],"0123456789")!=strlen(argv[i]))return 2;
    unsigned w=atoi(argv[1]),h=atoi(argv[2]),seed=atoi(argv[3]);if(!w||w>64||!h||h>16||seed>255)return 2;
    NSDictionary *props=@{(__bridge NSString *)kIOSurfaceWidth:@(w),(__bridge NSString *)kIOSurfaceHeight:@(h),(__bridge NSString *)kIOSurfaceBytesPerElement:@4,(__bridge NSString *)kIOSurfacePixelFormat:@(0x42475241)};
    IOSurfaceRef a=IOSurfaceCreate((__bridge CFDictionaryRef)props),b=IOSurfaceCreate((__bridge CFDictionaryRef)props);if(!a||!b)return 3;
    NSData *first=fill(a,seed),*second=fill(b,(seed+1)&255);if(!first||!second)return 4;
    unsigned aid=IOSurfaceGetID(a),bid=IOSurfaceGetID(b);mach_port_t old=IOSurfaceCreateMachPort(a),replacement=MACH_PORT_NULL;
    if(!MACH_PORT_VALID(old))return 5;
    unsigned live=lookup(old);
    if(retained){CFRelease(a);a=NULL;}else if(mach_port_deallocate(mach_task_self(),old))return 6;
    unsigned retired=lookup(old);NSMutableArray *observations=[NSMutableArray array];
    for(unsigned i=0;i<128;i++) {
        replacement=IOSurfaceCreateMachPort(b);if(!MACH_PORT_VALID(replacement))return 7;
        mach_port_urefs_t count=0;if(mach_port_get_refs(mach_task_self(),replacement,MACH_PORT_RIGHT_SEND,&count))return 7;
        unsigned current=lookup(replacement),stale_now=lookup(old);
        if(mach_port_deallocate(mach_task_self(),replacement))return 7;
        mach_port_type_t t=0;kern_return_t gone=mach_port_type(mach_task_self(),replacement,&t);
        [observations addObject:@{@"name":@(replacement),@"current_id":@(current),@"stale_id":@(stale_now),@"send_refs":@(count),@"removed":@((BOOL)(gone==KERN_INVALID_NAME))}];
    }
    replacement=IOSurfaceCreateMachPort(b);if(!MACH_PORT_VALID(replacement))return 7;
    unsigned stale=lookup(old),previous=lookup(replacement);IOSurfaceRef read=IOSurfaceLookupFromMachPort(replacement);if(!read)return 8;
    if(IOSurfaceLock(read,kIOSurfaceLockReadOnly,NULL))return 9;
    NSData *actual=[NSData dataWithBytes:IOSurfaceGetBaseAddress(read) length:IOSurfaceGetAllocSize(read)];
    if(IOSurfaceUnlock(read,kIOSurfaceLockReadOnly,NULL))return 9;CFRelease(read);
    mach_port_urefs_t refs=0;kern_return_t ref_status=mach_port_get_refs(mach_task_self(),replacement,MACH_PORT_RIGHT_SEND,&refs);
    kern_return_t released=mach_port_deallocate(mach_task_self(),replacement);mach_port_type_t kind=0;kern_return_t removed=mach_port_type(mach_task_self(),replacement,&kind);
    NSData *retainedBytes=nil;mach_port_urefs_t retainedRefs=0;kern_return_t retainedRelease=0;BOOL retainedRemoved=NO;
    if(retained) {
        IOSurfaceRef delayed=IOSurfaceLookupFromMachPort(old);if(!delayed)return 11;
        if(IOSurfaceLock(delayed,kIOSurfaceLockReadOnly,NULL))return 11;
        retainedBytes=[NSData dataWithBytes:IOSurfaceGetBaseAddress(delayed) length:IOSurfaceGetAllocSize(delayed)];
        if(IOSurfaceUnlock(delayed,kIOSurfaceLockReadOnly,NULL))return 11;CFRelease(delayed);
        if(mach_port_get_refs(mach_task_self(),old,MACH_PORT_RIGHT_SEND,&retainedRefs))return 11;
        retainedRelease=mach_port_deallocate(mach_task_self(),old);
        mach_port_type_t t=0;retainedRemoved=mach_port_type(mach_task_self(),old,&t)==KERN_INVALID_NAME;
    }
    NSMutableDictionary *r=[@{@"width":@(w),@"height":@(h),@"seed":@(seed),@"stride":@(IOSurfaceGetBytesPerRow(b)),@"allocation":@(IOSurfaceGetAllocSize(b)),@"first_id":@(aid),@"second_id":@(bid),@"live_lookup":@(live),@"retired_lookup":@(retired),@"stale_lookup":@(stale),@"previous_name_lookup":@(previous),@"old_name":@(old),@"replacement_name":@(replacement),@"observations":observations,@"ref_status":@(ref_status),@"send_refs":@(refs),@"release_status":@(released),@"name_removed":@((BOOL)(removed==KERN_INVALID_NAME)),@"first_base64":[first base64EncodedStringWithOptions:0],@"second_base64":[second base64EncodedStringWithOptions:0],@"stale_base64":[actual base64EncodedStringWithOptions:0]} mutableCopy];
    if(retained){r[@"retained_right"]=@YES;r[@"producer_cf_released"]=@YES;r[@"retained_refs"]=@(retainedRefs);r[@"retained_release_status"]=@(retainedRelease);r[@"retained_name_removed"]=@(retainedRemoved);r[@"retained_base64"]=[retainedBytes base64EncodedStringWithOptions:0];}
    if(a)CFRelease(a);CFRelease(b);NSData *json=[NSJSONSerialization dataWithJSONObject:r options:0 error:nil];if(!json)return 10;fwrite(json.bytes,1,json.length,stdout);return 0;
}}
