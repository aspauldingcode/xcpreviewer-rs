#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <unistd.h>
#include <stdatomic.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"check failed line %d\n",__LINE__);return 2;}}while(0)
@protocol EventPeer
-(void)probeHandle:(MTLSharedEventHandle*)handle reply:(void (^)(NSDictionary*))reply;
-(void)finish:(void (^)(BOOL))reply;
-(void)signalRetained:(BOOL)drop reply:(void (^)(NSDictionary*))reply;
@end
@interface Peer:NSObject<EventPeer,NSXPCListenerDelegate>
@property(strong) id<MTLDevice> device;
@property pid_t expectedParent;
@property(strong) id<MTLSharedEvent> retainedEvent;
@property pid_t acceptedParent;
@end
@implementation Peer
-(BOOL)listener:(NSXPCListener*)listener shouldAcceptNewConnection:(NSXPCConnection*)connection{
 if(connection.processIdentifier!=self.expectedParent)return NO;self.acceptedParent=connection.processIdentifier;
 connection.exportedInterface=[NSXPCInterface interfaceWithProtocol:@protocol(EventPeer)];connection.exportedObject=self;[connection resume];return YES;
}
-(void)finish:(void (^)(BOOL))reply{reply(YES);dispatch_after(dispatch_time(DISPATCH_TIME_NOW,100*NSEC_PER_MSEC),dispatch_get_global_queue(QOS_CLASS_DEFAULT,0),^{exit(0);});}
-(void)probeHandle:(MTLSharedEventHandle*)handle reply:(void (^)(NSDictionary*))reply{
 self.retainedEvent=[self.device newSharedEventWithHandle:handle];
 reply(@{@"pid":@(getpid()),@"accepted_parent":@(self.acceptedParent),@"present":[NSNumber numberWithBool:self.retainedEvent!=nil],@"token":@((uintptr_t)(__bridge void*)self.retainedEvent),@"value":@(self.retainedEvent.signaledValue)});
}
-(void)signalRetained:(BOOL)drop reply:(void (^)(NSDictionary*))reply{
 uintptr_t token=(uintptr_t)(__bridge void*)self.retainedEvent;BOOL present=self.retainedEvent!=nil;
 if(drop){self.retainedEvent=nil;id<MTLSharedEvent>wrong=[self.device newSharedEvent];wrong.signaledValue=7;}
 else self.retainedEvent.signaledValue=7;
 reply(@{@"pid":@(getpid()),@"accepted_parent":@(self.acceptedParent),@"before_present":[NSNumber numberWithBool:present],@"after_present":[NSNumber numberWithBool:self.retainedEvent!=nil],@"before_token":@(token),@"after_token":@((uintptr_t)(__bridge void*)self.retainedEvent),@"value":self.retainedEvent?@(self.retainedEvent.signaledValue):(id)[NSNull null]});
}
@end
int main(int argc,char**argv){alarm(12);@autoreleasepool{
 CHECK(argc==3||argc==4);NSString*service=[NSString stringWithUTF8String:argv[2]];
 if(!strcmp(argv[1],"--peer")){CHECK(argc==4);Peer*peer=[Peer new];peer.device=MTLCreateSystemDefaultDevice();CHECK(peer.device);peer.expectedParent=atoi(argv[3]);NSXPCListener*listener=[[NSXPCListener alloc]initWithMachServiceName:service];listener.delegate=peer;[listener resume];[[NSRunLoop currentRunLoop]run];return 2;}
 BOOL drop=!strcmp(argv[1],"--parent-drop");CHECK((drop||!strcmp(argv[1],"--parent"))&&getchar()==10);
 id<MTLDevice> device=MTLCreateSystemDefaultDevice();CHECK(device);id<MTLSharedEvent> event=[device newSharedEvent];CHECK(event);event.signaledValue=3;
 MTLSharedEventHandle*handle=[event newSharedEventHandle];CHECK(handle);id<MTLSharedEvent>recovery=[device newSharedEventWithHandle:handle];CHECK(recovery);
 NSXPCConnection*connection=[[NSXPCConnection alloc]initWithMachServiceName:service options:0];connection.remoteObjectInterface=[NSXPCInterface interfaceWithProtocol:@protocol(EventPeer)];[connection resume];
 id<MTLCommandQueue>queue=[device newCommandQueue];id<MTLBuffer>buffer=[device newBufferWithLength:16384 options:MTLResourceStorageModeShared];CHECK(queue&&buffer);memset(buffer.contents,0x5c,16384);NSData*before=[NSData dataWithBytes:buffer.contents length:16384];
 id<MTLCommandBuffer>command=[queue commandBuffer];[command encodeWaitForEvent:event value:7];id<MTLBlitCommandEncoder>blit=[command blitCommandEncoder];for(int y=0;y<6;y++)[blit fillBuffer:buffer range:NSMakeRange(y*256,44) value:0x77];[blit endEncoding];
 dispatch_semaphore_t done=dispatch_semaphore_create(0),response=dispatch_semaphore_create(0);__block NSData*after=nil;__block NSDictionary*reply=nil;__block NSString*rpcError=nil;__block long status=0;atomic_int callbackCount=0;atomic_int*count=&callbackCount;
 [command addCompletedHandler:^(id<MTLCommandBuffer>c){status=c.status;atomic_fetch_add(count,1);if(c.status==MTLCommandBufferStatusCompleted)after=[NSData dataWithBytes:buffer.contents length:16384];dispatch_semaphore_signal(done);}];[command commit];
 long pending=dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,20*NSEC_PER_MSEC));int pendingCallbacks=atomic_load(count);uint64_t pendingValue=event.signaledValue;
 id<EventPeer>proxy=[connection remoteObjectProxyWithErrorHandler:^(NSError*e){rpcError=e.domain;dispatch_semaphore_signal(response);}];[proxy probeHandle:handle reply:^(NSDictionary*d){reply=d;dispatch_semaphore_signal(response);}];
 long replyWait=dispatch_semaphore_wait(response,dispatch_time(DISPATCH_TIME_NOW,3*NSEC_PER_SEC));uint64_t valueAfterRPC=event.signaledValue;pid_t peerPID=connection.processIdentifier;
 [connection invalidate];connection=nil;proxy=nil;handle=nil;event=nil;
 uint64_t afterDisconnect=recovery.signaledValue;long disconnectedWait=dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,20*NSEC_PER_MSEC));int disconnectedCallbacks=atomic_load(count);
 NSXPCConnection*second=[[NSXPCConnection alloc]initWithMachServiceName:service options:0];second.remoteObjectInterface=[NSXPCInterface interfaceWithProtocol:@protocol(EventPeer)];[second resume];dispatch_semaphore_t secondResponse=dispatch_semaphore_create(0);__block NSDictionary*secondReply=nil;__block NSString*secondError=nil;
 id<EventPeer>secondProxy=[second remoteObjectProxyWithErrorHandler:^(NSError*e){secondError=e.domain;dispatch_semaphore_signal(secondResponse);}];[secondProxy signalRetained:drop reply:^(NSDictionary*d){secondReply=d;dispatch_semaphore_signal(secondResponse);}];long secondWait=dispatch_semaphore_wait(secondResponse,dispatch_time(DISPATCH_TIME_NOW,3*NSEC_PER_SEC));pid_t secondPID=second.processIdentifier;uint64_t afterSecond=recovery.signaledValue;
 long rpcPending=0;int rpcPendingCallbacks=0;if(afterSecond==3){rpcPending=dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,20*NSEC_PER_MSEC));rpcPendingCallbacks=atomic_load(count);}
 // Always release the owned GPU gate, including failed XPC or metadata controls.
 recovery.signaledValue=7;long completion=dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC));
 dispatch_semaphore_t finish=dispatch_semaphore_create(0);__block BOOL finishReply=NO;[secondProxy finish:^(BOOL yes){finishReply=yes;dispatch_semaphore_signal(finish);}];long finishWait=dispatch_semaphore_wait(finish,dispatch_time(DISPATCH_TIME_NOW,NSEC_PER_SEC));[second invalidate];
 NSDictionary*out=@{@"pid":@(getpid()),@"device":device.name,@"unified_memory":@(device.hasUnifiedMemory),@"peer_pid":@(peerPID),@"drop":[NSNumber numberWithBool:drop],@"after_disconnect":@(afterDisconnect),@"disconnected_wait":@(disconnectedWait),@"disconnected_callbacks":@(disconnectedCallbacks),@"second_pid":@(secondPID),@"second_wait":@(secondWait),@"second_error":secondError?: (id)[NSNull null],@"second_reply":secondReply?: (id)[NSNull null],@"after_second":@(afterSecond),@"original_owners_cleared":[NSNumber numberWithBool:handle==nil&&event==nil&&connection==nil],@"rpc_pending_wait":@(rpcPending),@"rpc_pending_callbacks":@(rpcPendingCallbacks),@"finish_wait":@(finishWait),@"finish_reply":@(finishReply),@"pending_timeout":[NSNumber numberWithBool:pending!=0],@"pending_callbacks":@(pendingCallbacks),@"pending_value":@(pendingValue),@"reply_wait":@(replyWait),@"rpc_error":rpcError?: (id)[NSNull null],@"reply":reply?: (id)[NSNull null],@"value_after_rpc":@(valueAfterRPC),@"completion_wait":@(completion),@"completion_status":@(status),@"callbacks":@(atomic_load(count)),@"before":[before base64EncodedStringWithOptions:0],@"after":after?[after base64EncodedStringWithOptions:0]:(id)[NSNull null]};NSData*j=[NSJSONSerialization dataWithJSONObject:out options:NSJSONWritingSortedKeys error:NULL];CHECK(j);fwrite(j.bytes,1,j.length,stdout);fputc('\n',stdout);CHECK(completion==0);return 0;
}}
