#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <unistd.h>
#include <stdatomic.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"check failed line %d\n",__LINE__);return 2;}}while(0)
static NSString *snapshot(id<MTLBuffer>b){return [[NSData dataWithBytes:b.contents length:b.length] base64EncodedStringWithOptions:0];}
typedef struct{atomic_int count;atomic_int status;uintptr_t token;} Completion;
int main(void){alarm(12);@autoreleasepool{
 id<MTLDevice>device=MTLCreateSystemDefaultDevice();CHECK(device&&device.hasUnifiedMemory);NSMutableArray*rows=[NSMutableArray array];
 for(unsigned mode=0;mode<2;mode++){
  __weak id<MTLBuffer>weakBuffer=nil;__weak id<MTLCommandBuffer>weakCommand=nil;
  NSMutableDictionary*out=[@{@"mode":mode?@"committed-timeout":@"encoded-uncommitted",@"submitted":[NSNumber numberWithBool:mode!=0]} mutableCopy];
  Completion completion={0};__block NSString*completedFrame=nil;dispatch_semaphore_t done=dispatch_semaphore_create(0);
  @autoreleasepool{
   id<MTLCommandQueue>queue=[device newCommandQueue];id<MTLSharedEvent>event=[device newSharedEvent];CHECK(queue&&event);
   @autoreleasepool{
    id<MTLBuffer>buffer=[device newBufferWithLength:16384 options:MTLResourceStorageModeShared];CHECK(buffer);memset(buffer.contents,0x5c,buffer.length);weakBuffer=buffer;
    out[@"token_before"]=@((uintptr_t)(__bridge void*)buffer);out[@"before"]=snapshot(buffer);
    id<MTLCommandBuffer>command=[queue commandBuffer];CHECK(command&&command.retainedReferences);weakCommand=command;out[@"retained_references"]=@(command.retainedReferences);
    [command encodeWaitForEvent:event value:1];id<MTLBlitCommandEncoder>encoder=[command blitCommandEncoder];CHECK(encoder);
    for(unsigned y=0;y<6;y++)[encoder fillBuffer:buffer range:NSMakeRange(y*256,44) value:0x77];[encoder endEncoding];encoder=nil;
    Completion*state=&completion;
    [command addCompletedHandler:^(id<MTLCommandBuffer>b){@autoreleasepool{
     atomic_store(&state->status,(int)b.status);id<MTLBuffer>observed=weakBuffer;
     if(b.status==MTLCommandBufferStatusCompleted&&observed){state->token=(uintptr_t)(__bridge void*)observed;completedFrame=snapshot(observed);}
     atomic_fetch_add(&state->count,1);dispatch_semaphore_signal(done);
    }}];
    buffer=nil;if(mode)[command commit];command=nil;
   }
   out[@"weak_buffer_after_construction_pool"]=[NSNumber numberWithBool:weakBuffer!=nil];out[@"weak_command_after_construction_pool"]=[NSNumber numberWithBool:weakCommand!=nil];
   out[@"event_before_release"]=@(event.signaledValue);
   if(mode){
    long timed=dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,20*NSEC_PER_MSEC));
    out[@"bounded_wait_timed_out"]=[NSNumber numberWithBool:timed!=0];out[@"callbacks_before_release"]=@(atomic_load(&completion.count));
    // Always release owned gate before validating the negative control. No pending CPU data read.
    event.signaledValue=1;
    long finished=dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC));CHECK(timed!=0&&finished==0);
    out[@"completion_status"]=@(atomic_load(&completion.status));out[@"token_in_callback"]=@(completion.token);out[@"after"]=completedFrame?: (id)[NSNull null];
   }else{out[@"bounded_wait_timed_out"]=[NSNull null];out[@"callbacks_before_release"]=@(atomic_load(&completion.count));out[@"completion_status"]=@(atomic_load(&completion.status));out[@"token_in_callback"]=@(completion.token);out[@"after"]=[NSNull null];}
   out[@"callbacks_after_release"]=@(atomic_load(&completion.count));out[@"event_after_release"]=@(event.signaledValue);
  }
  out[@"weak_buffer_after_queue_pool"]=[NSNumber numberWithBool:weakBuffer!=nil];out[@"weak_command_after_queue_pool"]=[NSNumber numberWithBool:weakCommand!=nil];[rows addObject:out];
 }
 NSDictionary*out=@{@"device":device.name,@"unified_memory":@(device.hasUnifiedMemory),@"allocation_bytes":@16384,@"rows":rows};NSData*j=[NSJSONSerialization dataWithJSONObject:out options:NSJSONWritingSortedKeys error:NULL];CHECK(j);fwrite(j.bytes,1,j.length,stdout);fputc('\n',stdout);return 0;
}}
