#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <unistd.h>
#include <stdatomic.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"check failed line %d\n",__LINE__);return 2;}}while(0)
@protocol EventPeer
-(void)probeHandle:(MTLSharedEventHandle*)handle reply:(void (^)(NSDictionary*))reply;
@end
@interface Peer:NSObject<EventPeer,NSXPCListenerDelegate>
@property(strong) id<MTLDevice> device;
@end
@implementation Peer
-(BOOL)listener:(NSXPCListener*)listener shouldAcceptNewConnection:(NSXPCConnection*)connection{
 connection.exportedInterface=[NSXPCInterface interfaceWithProtocol:@protocol(EventPeer)];connection.exportedObject=self;[connection resume];return YES;
}
-(void)probeHandle:(MTLSharedEventHandle*)handle reply:(void (^)(NSDictionary*))reply{
 id<MTLSharedEvent> imported=[self.device newSharedEventWithHandle:handle];
 if(!imported){reply(@{@"imported":@NO});return;}
 uint64_t before=imported.signaledValue;id<MTLSharedEvent> wrong=[self.device newSharedEvent];wrong.signaledValue=99;
 uint64_t afterWrong=imported.signaledValue;imported.signaledValue=7;
 reply(@{@"imported":@YES,@"pid":@(getpid()),@"before":@(before),@"wrong_event":@(wrong.signaledValue),@"after_wrong":@(afterWrong),@"after":@(imported.signaledValue)});
}
@end
int main(void){alarm(12);@autoreleasepool{
 id<MTLDevice> device=MTLCreateSystemDefaultDevice();CHECK(device);id<MTLSharedEvent> event=[device newSharedEvent];CHECK(event);event.signaledValue=3;
 MTLSharedEventHandle*handle=[event newSharedEventHandle];CHECK(handle);
 NSMutableDictionary*archive=[NSMutableDictionary dictionary];
 @try{NSError*error=nil;NSData*data=[NSKeyedArchiver archivedDataWithRootObject:handle requiringSecureCoding:YES error:&error];archive[@"produced_data"]=[NSNumber numberWithBool:data!=nil];archive[@"bytes"]=@(data.length);archive[@"error_domain"]=error.domain?: (id)[NSNull null];archive[@"error_code"]=error?@(error.code):(id)[NSNull null];archive[@"exception_name"]=[NSNull null];}
 @catch(NSException*exception){archive[@"produced_data"]=@NO;archive[@"bytes"]=@0;archive[@"error_domain"]=[NSNull null];archive[@"error_code"]=[NSNull null];archive[@"exception_name"]=exception.name;}
 NSError*error=nil;NSData*positive=[NSKeyedArchiver archivedDataWithRootObject:@"owned secure-coding control" requiringSecureCoding:YES error:&error];CHECK(positive&&!error);
 NSString*decoded=[NSKeyedUnarchiver unarchivedObjectOfClass:NSString.class fromData:positive error:&error];CHECK([decoded isEqual:@"owned secure-coding control"]&&!error);
 Peer*peer=[Peer new];peer.device=device;NSXPCListener*listener=[NSXPCListener anonymousListener];listener.delegate=peer;[listener resume];NSXPCConnection*connection=[[NSXPCConnection alloc]initWithListenerEndpoint:listener.endpoint];connection.remoteObjectInterface=[NSXPCInterface interfaceWithProtocol:@protocol(EventPeer)];[connection resume];
 id<MTLCommandQueue>queue=[device newCommandQueue];id<MTLBuffer>buffer=[device newBufferWithLength:16384 options:MTLResourceStorageModeShared];CHECK(queue&&buffer);memset(buffer.contents,0x5c,16384);NSData*before=[NSData dataWithBytes:buffer.contents length:16384];
 id<MTLCommandBuffer>command=[queue commandBuffer];[command encodeWaitForEvent:event value:7];id<MTLBlitCommandEncoder>blit=[command blitCommandEncoder];for(int y=0;y<6;y++)[blit fillBuffer:buffer range:NSMakeRange(y*256,44) value:0x77];[blit endEncoding];
 dispatch_semaphore_t done=dispatch_semaphore_create(0),response=dispatch_semaphore_create(0);__block NSData*after=nil;__block NSDictionary*reply=nil;__block NSString*rpcError=nil;__block long status=0;atomic_int callbackCount=0;atomic_int*count=&callbackCount;
 [command addCompletedHandler:^(id<MTLCommandBuffer>c){status=c.status;atomic_fetch_add(count,1);if(c.status==MTLCommandBufferStatusCompleted)after=[NSData dataWithBytes:buffer.contents length:16384];dispatch_semaphore_signal(done);}];[command commit];
 long pending=dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,20*NSEC_PER_MSEC));int pendingCallbacks=atomic_load(count);uint64_t pendingValue=event.signaledValue;
 id<EventPeer>proxy=[connection remoteObjectProxyWithErrorHandler:^(NSError*e){rpcError=e.domain;dispatch_semaphore_signal(response);}];[proxy probeHandle:handle reply:^(NSDictionary*d){reply=d;dispatch_semaphore_signal(response);}];
 long replyWait=dispatch_semaphore_wait(response,dispatch_time(DISPATCH_TIME_NOW,3*NSEC_PER_SEC));uint64_t valueAfterRPC=event.signaledValue;
 // Always release the owned GPU gate, including failed XPC or metadata controls.
 event.signaledValue=7;long completion=dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC));
 [connection invalidate];[listener invalidate];
 NSDictionary*out=@{@"pid":@(getpid()),@"device":device.name,@"unified_memory":@(device.hasUnifiedMemory),@"archive":archive,@"secure_string":decoded,@"pending_timeout":[NSNumber numberWithBool:pending!=0],@"pending_callbacks":@(pendingCallbacks),@"pending_value":@(pendingValue),@"reply_wait":@(replyWait),@"rpc_error":rpcError?: (id)[NSNull null],@"reply":reply?: (id)[NSNull null],@"value_after_rpc":@(valueAfterRPC),@"completion_wait":@(completion),@"completion_status":@(status),@"callbacks":@(atomic_load(count)),@"before":[before base64EncodedStringWithOptions:0],@"after":after?[after base64EncodedStringWithOptions:0]:(id)[NSNull null]};NSData*j=[NSJSONSerialization dataWithJSONObject:out options:NSJSONWritingSortedKeys error:NULL];CHECK(j);fwrite(j.bytes,1,j.length,stdout);fputc('\n',stdout);CHECK(completion==0);return 0;
}}
