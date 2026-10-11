// Never submit the unretained command: buffer lifetime is the measured boundary.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <unistd.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"check failed line %d\n",__LINE__);return 2;}}while(0)
static NSString *snapshot(id<MTLBuffer>b){return [[NSData dataWithBytes:b.contents length:b.length] base64EncodedStringWithOptions:0];}
int main(void){alarm(10);@autoreleasepool{
 id<MTLDevice>device=MTLCreateSystemDefaultDevice();CHECK(device&&device.hasUnifiedMemory);NSMutableArray*rows=[NSMutableArray array];
 NSArray*modes=@[@"cpu-only",@"retained-unencoded",@"retained-encoded",@"unretained-encoded"];
 for(unsigned mode=0;mode<4;mode++){
  __weak id<MTLBuffer>weakBuffer=nil;__weak id<MTLCommandBuffer>weakCommand=nil;NSMutableDictionary*out=[@{@"mode":modes[mode],@"submitted":@NO} mutableCopy];
  @autoreleasepool{
   id<MTLCommandQueue>queue=mode?[device newCommandQueue]:nil;id<MTLCommandBuffer>command=nil;
   if(mode){CHECK(queue);command=mode==3?[queue commandBufferWithUnretainedReferences]:[queue commandBuffer];CHECK(command);weakCommand=command;out[@"retained_references"]=@(command.retainedReferences);}
   else out[@"retained_references"]=[NSNull null];
   @autoreleasepool{
    id<MTLBuffer>buffer=[device newBufferWithLength:16384 options:MTLResourceStorageModeShared];CHECK(buffer);memset(buffer.contents,0x5c,buffer.length);weakBuffer=buffer;
    out[@"token_before"]=@((uintptr_t)(__bridge void*)buffer);out[@"before"]=snapshot(buffer);
    if(mode>=2){id<MTLBlitCommandEncoder>encoder=[command blitCommandEncoder];CHECK(encoder);for(unsigned y=0;y<6;y++)[encoder fillBuffer:buffer range:NSMakeRange(y*256,44) value:0x77];[encoder endEncoding];encoder=nil;}
    buffer=nil;
   }
out[@"weak_buffer_alive_after_cpu_drop"]=[NSNumber numberWithBool:weakBuffer!=nil];out[@"token_after_cpu_drop"]=@((uintptr_t)(__bridge void*)weakBuffer);out[@"weak_command_alive_before_pool_drain"]=[NSNumber numberWithBool:weakCommand!=nil];
   out[@"command_status"]=command?@(command.status):[NSNull null];
   // No commit in any mode. Never dereference an expired weak object.
   out[@"after"]=weakBuffer?snapshot(weakBuffer):(id)[NSNull null];command=nil;
  }
  out[@"weak_buffer_alive_after_pool_drain"]=[NSNumber numberWithBool:weakBuffer!=nil];out[@"weak_command_alive_after_pool_drain"]=[NSNumber numberWithBool:weakCommand!=nil];[rows addObject:out];
 }
 NSDictionary*out=@{@"device":device.name,@"unified_memory":@(device.hasUnifiedMemory),@"allocation_bytes":@16384,@"rows":rows};NSData*j=[NSJSONSerialization dataWithJSONObject:out options:NSJSONWritingSortedKeys error:NULL];CHECK(j);fwrite(j.bytes,1,j.length,stdout);fputc('\n',stdout);return 0;
}}
