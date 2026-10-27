#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#import <xpc/xpc.h>
#include <unistd.h>
static xpc_connection_t listener,client,remote;static dispatch_queue_t queue;
static dispatch_semaphore_t received;
static NSMutableArray *eventDescriptions;static NSData *messageData;static int peerCount,dictCount,identityOK;
void *owned_create_client(void) {
 eventDescriptions=[NSMutableArray array];queue=dispatch_queue_create("owned.previews.peer",DISPATCH_QUEUE_SERIAL);received=dispatch_semaphore_create(0);
 listener=xpc_connection_create(NULL,queue);if(!listener)return NULL;
 xpc_connection_set_event_handler(listener,^(xpc_object_t event){
  if(xpc_get_type(event)!=XPC_TYPE_CONNECTION)return;
  remote=event;peerCount++;
  xpc_connection_set_event_handler(remote,^(xpc_object_t message){
   if(xpc_get_type(message)!=XPC_TYPE_DICTIONARY){[eventDescriptions addObject:message==XPC_ERROR_CONNECTION_INVALID?@"connectionInvalidated":message==XPC_ERROR_CONNECTION_INTERRUPTED?@"connectionInterrupted":@"nonDictionary"];return;}
   dictCount++;identityOK=xpc_connection_get_pid(remote)==getpid();
   size_t n=0;const void *b=xpc_dictionary_get_data(message,"data",&n);messageData=b?[NSData dataWithBytes:b length:n]:nil;
   xpc_object_t reply=xpc_dictionary_create_reply(message);
   if(reply){NSData*d=[NSPropertyListSerialization dataWithPropertyList:@{@"ownedReply":@42} format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL];xpc_dictionary_set_data(reply,"data",d.bytes,d.length);xpc_connection_send_message(remote,reply);}
   dispatch_semaphore_signal(received);
  });xpc_connection_activate(remote);
 });xpc_connection_activate(listener);
 xpc_object_t endpoint=xpc_endpoint_create(listener);client=xpc_connection_create_from_endpoint(endpoint);
 return client?(__bridge_retained void*)client:NULL;
}
static BOOL method(id target,SEL sel,unsigned args){Method m=class_getInstanceMethod(object_getClass(target),sel);if(!m||method_getNumberOfArguments(m)!=args)return NO;char *t=method_copyReturnType(m);BOOL ok=!strcmp(t,"@");free(t);return ok;}
void *owned_uv_create(NSDictionary *d){Class c=NSClassFromString(@"UVPropertyList");if(!c)return NULL;id o=[c alloc];SEL s=NSSelectorFromString(@"initWithDictionary:");if(!method(o,s,3))return NULL;NSInvocation*i=[NSInvocation invocationWithMethodSignature:[o methodSignatureForSelector:s]];i.target=o;i.selector=s;[i setArgument:&d atIndex:2];[i invoke];__unsafe_unretained id v=nil;[i getReturnValue:&v];return (__bridge_retained void*)v;}
NSDictionary *owned_uv_dictionary(const void *p){id o=(__bridge id)p;SEL s=NSSelectorFromString(@"dictionary");if(!method(o,s,2))return nil;NSInvocation*i=[NSInvocation invocationWithMethodSignature:[o methodSignatureForSelector:s]];i.target=o;i.selector=s;[i invoke];__unsafe_unretained id v=nil;[i getReturnValue:&v];return [v isKindOfClass:[NSDictionary class]]?v:nil;}
void owned_obj_release(const void*p){if(p)CFBridgingRelease(p);}
NSDictionary *owned_peer_result(void){long v=dispatch_semaphore_wait(received,dispatch_time(DISPATCH_TIME_NOW,2*NSEC_PER_SEC));__block NSDictionary *snapshot;dispatch_sync(queue,^{snapshot=@{@"receiveTimedOut":@(v!=0),@"peers":@(peerCount),@"dictionaries":@(dictCount),@"sameProcessPeer":@(identityOK),@"messageData":messageData?:[NSData data],@"peerEvents":[eventDescriptions copy]?:@[]};});return snapshot;}
void owned_peer_close(void){if(client){xpc_connection_cancel(client);client=NULL;}if(remote){xpc_connection_cancel(remote);remote=NULL;}if(listener){xpc_connection_cancel(listener);listener=NULL;}}

unsigned long owned_object_size(const void*p){return class_getInstanceSize(object_getClass((__bridge id)p));}
