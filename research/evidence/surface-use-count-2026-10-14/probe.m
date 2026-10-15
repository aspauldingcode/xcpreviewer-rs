// Owned public IOSurface use-count and right-lifetime contrast. No reclamation probe.
#import <Foundation/Foundation.h>
#import <IOSurface/IOSurface.h>
#import <mach/mach.h>
#import <unistd.h>
static NSDictionary *state(IOSurfaceRef a,IOSurfaceRef b,NSString *phase){
 return @{ @"phase":phase,@"original_count":@(IOSurfaceGetUseCount(a)),@"alias_count":@(IOSurfaceGetUseCount(b)),@"original_in_use":@((BOOL)IOSurfaceIsInUse(a)),@"alias_in_use":@((BOOL)IOSurfaceIsInUse(b))};
}
static BOOL save(IOSurfaceRef s,NSString *file){
 if(IOSurfaceLock(s,kIOSurfaceLockReadOnly,NULL))return NO;
 NSData *d=[NSData dataWithBytes:IOSurfaceGetBaseAddress(s) length:IOSurfaceGetAllocSize(s)];
 if(IOSurfaceUnlock(s,kIOSurfaceLockReadOnly,NULL))return NO;
 return [d writeToFile:file atomically:YES];
}
int main(int argc,const char **argv){@autoreleasepool{
 alarm(5);if(argc!=3)return 2;int mode=atoi(argv[1]);if(mode<0||mode>1)return 2;
 NSString *folder=@(argv[2]);size_t w=mode?13:17,h=mode?7:9;unsigned seed=mode?178:49;
 NSDictionary *props=@{(__bridge NSString*)kIOSurfaceWidth:@(w),(__bridge NSString*)kIOSurfaceHeight:@(h),(__bridge NSString*)kIOSurfaceBytesPerElement:@4,(__bridge NSString*)kIOSurfacePixelFormat:@((uint32_t)0x42475241)};
 IOSurfaceRef a=IOSurfaceCreate((__bridge CFDictionaryRef)props);if(!a)return 3;
 size_t stride=IOSurfaceGetBytesPerRow(a),n=IOSurfaceGetAllocSize(a);if(stride<w*4||stride>65536||n<stride*h||n>1048576)return 4;
 if(IOSurfaceLock(a,0,NULL))return 5;uint8_t *p=IOSurfaceGetBaseAddress(a);memset(p,0xa5,n);
 for(size_t y=0;y<h;y++)for(size_t x=0;x<w;x++)for(size_t c=0;c<4;c++)p[y*stride+x*4+c]=c==3?255:(seed+x*17+y*31+c*53)&255;
 if(IOSurfaceUnlock(a,0,NULL))return 6;
 mach_port_t port=IOSurfaceCreateMachPort(a);IOSurfaceRef b=IOSurfaceLookupFromMachPort(port);if(!b)return 7;
 BOOL same=IOSurfaceGetID(a)==IOSurfaceGetID(b);mach_port_urefs_t refs=0;int refs_rc=mach_port_get_refs(mach_task_self(),port,MACH_PORT_RIGHT_SEND,&refs);
 NSMutableArray *states=[NSMutableArray arrayWithObject:state(a,b,@"baseline")];
 if(!save(b,[folder stringByAppendingPathComponent:@"baseline.raw"]))return 8;
 IOSurfaceIncrementUseCount(a);[states addObject:state(a,b,@"increment-original")];
 IOSurfaceIncrementUseCount(mode?b:a);[states addObject:state(a,b,@"increment-second")];
 IOSurfaceDecrementUseCount(mode?b:a);[states addObject:state(a,b,@"decrement-second")];
 IOSurfaceDecrementUseCount(a);[states addObject:state(a,b,@"zero-with-right")];
 if(!save(b,[folder stringByAppendingPathComponent:@"zero.raw"]))return 9;
 int release=mach_port_deallocate(mach_task_self(),port);refs=0;int after_rc=mach_port_get_refs(mach_task_self(),port,MACH_PORT_RIGHT_SEND,&refs);
 CFRelease(a);a=NULL;int alias_count=IOSurfaceGetUseCount(b);BOOL alias_inuse=IOSurfaceIsInUse(b);
 if(!save(b,[folder stringByAppendingPathComponent:@"alias-only.raw"]))return 10;
 NSDictionary *d=@{@"mode":@(mode),@"width":@(w),@"height":@(h),@"seed":@(seed),@"stride":@(stride),@"allocation":@(n),@"same_id":@(same),@"initial_ref_status":@(refs_rc),@"release_status":@(release),@"final_ref_status":@(after_rc),@"final_send_refs":@(refs),@"states":states,@"alias_only_count":@(alias_count),@"alias_only_in_use":@(alias_inuse)};
 CFRelease(b);NSData *json=[NSJSONSerialization dataWithJSONObject:d options:NSJSONWritingSortedKeys error:NULL];return [json writeToFile:[folder stringByAppendingPathComponent:@"result.json"] atomically:YES]?0:11;
}}
