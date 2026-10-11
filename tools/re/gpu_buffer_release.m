// Owned ARC weak-object lifetime oracle; no physical memory reclamation claim.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <stdatomic.h>
#include <unistd.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"check failed line %d\n",__LINE__);return 2;}}while(0)
static NSString *snapshot(id<MTLBuffer>b){return [[NSData dataWithBytes:b.contents length:b.length] base64EncodedStringWithOptions:0];}
int main(void){alarm(20);@autoreleasepool{
 id<MTLDevice>device=MTLCreateSystemDefaultDevice();CHECK(device&&device.hasUnifiedMemory);
 NSMutableArray*rows=[NSMutableArray array];
 for(unsigned committed=0;committed<2;committed++){
  __weak id<MTLBuffer>weakBuffer=nil;__weak id<MTLCommandBuffer>weakCommand=nil;
  NSMutableDictionary*out=[@{@"mode":committed?@"committed-timeout":@"encoded-uncommitted"} mutableCopy];
  @autoreleasepool{
   id<MTLCommandQueue>queue=[device newCommandQueue];id<MTLSharedEvent>event=[device newSharedEvent];CHECK(queue&&event&&event.signaledValue==0);
   id<MTLBuffer>buffer=[device newBufferWithLength:16384 options:MTLResourceStorageModeShared];CHECK(buffer);memset(buffer.contents,0x5c,buffer.length);
   weakBuffer=buffer;out[@"token_before"]=@((uintptr_t)(__bridge void*)buffer);out[@"before"]=snapshot(buffer);
   id<MTLCommandBuffer>command=[queue commandBuffer];CHECK(command&&command.retainedReferences);weakCommand=command;
   [command encodeWaitForEvent:event value:1];id<MTLBlitCommandEncoder>encoder=[command blitCommandEncoder];CHECK(encoder);
   for(unsigned y=0;y<6;y++)[encoder fillBuffer:buffer range:NSMakeRange(y*256,44) value:0x77];[encoder endEncoding];encoder=nil;
   out[@"retained_references"]=@(command.retainedReferences);buffer=nil;
   out[@"weak_alive_after_cpu_drop"]=[NSNumber numberWithBool:weakBuffer!=nil];out[@"token_after_cpu_drop"]=@((uintptr_t)(__bridge void*)weakBuffer);
   dispatch_semaphore_t completed=dispatch_semaphore_create(0);__block atomic_uint callbacks=0;
   [command addCompletedHandler:^(id<MTLCommandBuffer>c){(void)c;atomic_fetch_add(&callbacks,1);dispatch_semaphore_signal(completed);}];
   if(committed){
    [command commit];long timed=dispatch_semaphore_wait(completed,dispatch_time(DISPATCH_TIME_NOW,20*NSEC_PER_MSEC));
    unsigned pendingCallbacks=atomic_load(&callbacks);out[@"timeout_observed"]=[NSNumber numberWithBool:timed!=0];out[@"callbacks_before_release"]=@(pendingCallbacks);out[@"status_before_release"]=@(command.status);out[@"event_before_release"]=@(event.signaledValue);out[@"weak_alive_pending"]=[NSNumber numberWithBool:weakBuffer!=nil];
    event.signaledValue=1;CHECK(timed!=0&&pendingCallbacks==0);CHECK(dispatch_semaphore_wait(completed,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC))==0&&atomic_load(&callbacks)==1&&command.status==4&&!command.error);
   }
   out[@"callback_count"]=@(atomic_load(&callbacks));out[@"status"]=@(command.status);out[@"event_after"]=@(event.signaledValue);out[@"error_absent"]=[NSNumber numberWithBool:command.error==nil];out[@"weak_alive_before_pool_drain"]=[NSNumber numberWithBool:weakBuffer!=nil];out[@"token_before_pool_drain"]=@((uintptr_t)(__bridge void*)weakBuffer);CHECK(weakBuffer);
   out[@"after"]=snapshot(weakBuffer);command=nil;
  }
  out[@"weak_buffer_alive_after_pool_drain"]=[NSNumber numberWithBool:weakBuffer!=nil];out[@"weak_command_alive_after_pool_drain"]=[NSNumber numberWithBool:weakCommand!=nil];[rows addObject:out];
 }
 NSDictionary*out=@{@"device":device.name,@"unified_memory":@(device.hasUnifiedMemory),@"rows":rows,@"allocation_bytes":@16384,@"row":@256,@"width_bytes":@44,@"height":@6,@"wait_ns":@20000000,@"completion_ns":@5000000000};
 NSData*j=[NSJSONSerialization dataWithJSONObject:out options:NSJSONWritingSortedKeys error:NULL];CHECK(j);fwrite(j.bytes,1,j.length,stdout);fputc('\n',stdout);return 0;
}}
