// Owned shared-buffer/event oracle; no Canvas/Mach protocol observation.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <stdatomic.h>
#include <unistd.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"check failed line %d\n",__LINE__);return 2;}}while(0)
static NSString *snapshot(id<MTLBuffer>b){return [[NSData dataWithBytes:b.contents length:b.length] base64EncodedStringWithOptions:0];}
static id<MTLCommandBuffer> writer(id<MTLCommandQueue>q,id<MTLBuffer>s,id<MTLSharedEvent>e,uint64_t wait,uint64_t signal,uint8_t color){
 id<MTLCommandBuffer>c=[q commandBuffer];[c encodeWaitForEvent:e value:wait];id<MTLBlitCommandEncoder>b=[c blitCommandEncoder];
 for(unsigned y=0;y<6;y++)[b fillBuffer:s range:NSMakeRange(y*256,44) value:color];[b endEncoding];[c encodeSignalEvent:e value:signal];return c;
}
static id<MTLCommandBuffer> reader(id<MTLCommandQueue>q,id<MTLBuffer>s,id<MTLBuffer>d,id<MTLSharedEvent>e,uint64_t wait){
 id<MTLCommandBuffer>c=[q commandBuffer];[c encodeWaitForEvent:e value:wait];id<MTLBlitCommandEncoder>b=[c blitCommandEncoder];
 for(unsigned y=0;y<6;y++)[b copyFromBuffer:s sourceOffset:y*256 toBuffer:d destinationOffset:y*256 size:44];[b endEncoding];return c;
}
int main(void){alarm(20);@autoreleasepool{
 id<MTLDevice>device=MTLCreateSystemDefaultDevice();CHECK(device&&device.hasUnifiedMemory);
 id<MTLBuffer>s=[device newBufferWithLength:16384 options:MTLResourceStorageModeShared],d=[device newBufferWithLength:16384 options:MTLResourceStorageModeShared];
 id<MTLCommandQueue>wq=[device newCommandQueue],rq=[device newCommandQueue];id<MTLSharedEvent>event=[device newSharedEvent];CHECK(s&&d&&wq&&rq&&event&&event.signaledValue==0&&wq!=rq);
 memset(s.contents,0xa5,s.length);memset(d.contents,0x5c,d.length);
 NSMutableDictionary*out=[@{@"device":device.name,@"unified_memory":@(device.hasUnifiedMemory),@"source_before":snapshot(s),@"destination_before":snapshot(d),@"allocation_bytes":@16384,@"row":@256,@"width_bytes":@44,@"height":@6,@"wait_ns":@20000000,@"completion_ns":@5000000000} mutableCopy];
 NSArray *tokens=@[@((uintptr_t)(__bridge void*)s),@((uintptr_t)(__bridge void*)d),@((uintptr_t)(__bridge void*)wq),@((uintptr_t)(__bridge void*)rq),@((uintptr_t)(__bridge void*)event)];out[@"resources_before"]=tokens;
 dispatch_semaphore_t wg=dispatch_semaphore_create(0),rg=dispatch_semaphore_create(0);__block atomic_uint wc=0,rc=0;
 id<MTLCommandBuffer>w=writer(wq,s,event,1,2,0x22),r=reader(rq,s,d,event,2);CHECK(w&&r);
 [w addCompletedHandler:^(id<MTLCommandBuffer>c){(void)c;atomic_fetch_add(&wc,1);dispatch_semaphore_signal(wg);}];
 [r addCompletedHandler:^(id<MTLCommandBuffer>c){(void)c;atomic_fetch_add(&rc,1);dispatch_semaphore_signal(rg);}];
 [r commit];[w commit];long pending=dispatch_semaphore_wait(rg,dispatch_time(DISPATCH_TIME_NOW,20*NSEC_PER_MSEC));unsigned callbacks=atomic_load(&rc);NSUInteger pendingStatus=r.status;uint64_t before=event.signaledValue;
 event.signaledValue=1;CHECK(pending!=0&&callbacks==0&&before==0&&(pendingStatus==2||pendingStatus==3));
 CHECK(dispatch_semaphore_wait(wg,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC))==0&&dispatch_semaphore_wait(rg,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC))==0);
 CHECK(atomic_load(&wc)==1&&atomic_load(&rc)==1&&w.status==4&&r.status==4&&!w.error&&!r.error&&event.signaledValue==2);
 out[@"first"]=@{@"pending":@(pending!=0),@"callbacks_before_release":@(callbacks),@"status_before_release":@(pendingStatus),@"event_before_release":@(before),@"event_after":@(event.signaledValue),@"writer_calls":@(atomic_load(&wc)),@"reader_calls":@(atomic_load(&rc)),@"writer_status":@(w.status),@"reader_status":@(r.status),@"source":snapshot(s),@"destination":snapshot(d)};
 dispatch_semaphore_t wg2=dispatch_semaphore_create(0),staleg=dispatch_semaphore_create(0),freshg=dispatch_semaphore_create(0);__block atomic_uint wc2=0,staleCalls=0,freshCalls=0;
 id<MTLCommandBuffer>w2=writer(wq,s,event,3,4,0x77),stale=reader(rq,s,d,event,2);CHECK(w2&&stale);
 [w2 addCompletedHandler:^(id<MTLCommandBuffer>c){(void)c;atomic_fetch_add(&wc2,1);dispatch_semaphore_signal(wg2);}];
 [stale addCompletedHandler:^(id<MTLCommandBuffer>c){(void)c;atomic_fetch_add(&staleCalls,1);dispatch_semaphore_signal(staleg);}];
 [w2 commit];[stale commit];CHECK(dispatch_semaphore_wait(staleg,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC))==0);
 CHECK(atomic_load(&staleCalls)==1&&atomic_load(&wc2)==0&&stale.status==4&&!stale.error&&event.signaledValue==2);
 out[@"stale"]=@{@"event":@(event.signaledValue),@"writer_calls":@(atomic_load(&wc2)),@"reader_calls":@(atomic_load(&staleCalls)),@"reader_status":@(stale.status),@"destination":snapshot(d)};
 event.signaledValue=3;CHECK(dispatch_semaphore_wait(wg2,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC))==0&&atomic_load(&wc2)==1&&w2.status==4&&!w2.error&&event.signaledValue==4);
 id<MTLCommandBuffer>fresh=reader(rq,s,d,event,4);CHECK(fresh);[fresh addCompletedHandler:^(id<MTLCommandBuffer>c){(void)c;atomic_fetch_add(&freshCalls,1);dispatch_semaphore_signal(freshg);}];[fresh commit];CHECK(dispatch_semaphore_wait(freshg,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC))==0&&atomic_load(&freshCalls)==1&&fresh.status==4&&!fresh.error);
 out[@"fresh"]=@{@"event":@(event.signaledValue),@"writer_calls":@(atomic_load(&wc2)),@"reader_calls":@(atomic_load(&freshCalls)),@"writer_status":@(w2.status),@"reader_status":@(fresh.status),@"source":snapshot(s),@"destination":snapshot(d)};
 out[@"resources_after"]=@[@((uintptr_t)(__bridge void*)s),@((uintptr_t)(__bridge void*)d),@((uintptr_t)(__bridge void*)wq),@((uintptr_t)(__bridge void*)rq),@((uintptr_t)(__bridge void*)event)];
 NSData*j=[NSJSONSerialization dataWithJSONObject:out options:NSJSONWritingSortedKeys error:NULL];CHECK(j);fwrite(j.bytes,1,j.length,stdout);fputc('\n',stdout);return 0;
}}
