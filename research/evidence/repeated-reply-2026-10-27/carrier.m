#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#include <xpc/xpc.h>
#include <dlfcn.h>
#include <unistd.h>
static id objectCall(id target,const char *name,const char *encoding,id argument) {
 SEL selector=sel_registerName(name);Method method=class_getInstanceMethod([target class],selector);
 if(!method || strcmp(method_getTypeEncoding(method),encoding)){fprintf(stderr,"UV signature guard failed\n");abort();}
 NSInvocation *inv=[NSInvocation invocationWithMethodSignature:[target methodSignatureForSelector:selector]];
 [inv setTarget:target];[inv setSelector:selector];
 if(inv.methodSignature.numberOfArguments==3)[inv setArgument:&argument atIndex:2];[inv invoke];
 id result=nil;[inv getReturnValue:&result];return result;
}
void *owned_exchange_uv(const void *requestPointer,const void *responsePointer,void **receiptPointer) {@autoreleasepool {
 NSData *request=(NSData *)requestPointer;NSData *response=(NSData *)responsePointer;
 NSDictionary *expected=[NSPropertyListSerialization propertyListWithData:request options:0 format:NULL error:NULL];
 NSCAssert([expected isKindOfClass:[NSDictionary class]],@"owned request dictionary");
 const char *path="/System/Library/PrivateFrameworks/PreviewsServices.framework/Versions/A/PreviewsServices";
 NSCAssert(dlopen(path,RTLD_NOW|RTLD_LOCAL)!=NULL,@"Services loaded");Class cls=NSClassFromString(@"UVPropertyList");
 NSCAssert(cls && !strcmp(class_getImageName(cls),path),@"UV image identity");
 dispatch_queue_t queue=dispatch_queue_create("owned.modern.sdk",DISPATCH_QUEUE_SERIAL);dispatch_group_t group=dispatch_group_create();dispatch_group_enter(group);
 __block xpc_connection_t peer=NULL;__block int requests=0,callbacks=0,errors=0;__block BOOL audit=NO;__block NSDictionary *decodedRequest=nil;__block id receivedUV=nil;__block BOOL replyBytesAvailable=NO,replyBytesEqual=NO;
 xpc_connection_t listener=xpc_connection_create(NULL,queue);NSCAssert(listener,@"listener");
 xpc_connection_set_event_handler(listener,^(xpc_object_t incoming){@autoreleasepool {
  if(xpc_get_type(incoming)!=XPC_TYPE_CONNECTION){errors++;return;}
  peer=(xpc_connection_t)incoming;xpc_retain(peer);audit=xpc_connection_get_pid(peer)==getpid();
  xpc_connection_set_event_handler(peer,^(xpc_object_t message){@autoreleasepool {
   if(xpc_get_type(message)!=XPC_TYPE_DICTIONARY){errors++;return;}
   id uv=objectCall([cls alloc],"initWithXpcDictionary:","@24@0:8@16",(id)message);
   NSDictionary *value=uv?objectCall(uv,"dictionary","@16@0:8",nil):nil;
   decodedRequest=[value retain];requests++;if(![value isEqual:expected])errors++;
   NSData *data=response;
   xpc_object_t reply=xpc_dictionary_create_reply(message);if(!reply){errors++;[uv release];return;}
   xpc_dictionary_set_data(reply,"data",data.bytes,data.length);xpc_connection_send_message(peer,reply);xpc_release(reply);[uv release];
  }});xpc_connection_activate(peer);
 }});xpc_connection_activate(listener);
 xpc_endpoint_t endpoint=xpc_endpoint_create(listener);xpc_connection_t client=xpc_connection_create_from_endpoint(endpoint);xpc_release(endpoint);NSCAssert(client,@"client");
 xpc_connection_set_event_handler(client,^(xpc_object_t e){if(xpc_get_type(e)==XPC_TYPE_ERROR)errors++;});xpc_connection_activate(client);
 xpc_object_t message=xpc_dictionary_create(NULL,NULL,0);xpc_dictionary_set_data(message,"data",request.bytes,request.length);
 xpc_connection_send_message_with_reply(client,message,queue,^(xpc_object_t response){@autoreleasepool {
  callbacks++;
  if(xpc_get_type(response)==XPC_TYPE_DICTIONARY){
   id uv=objectCall([cls alloc],"initWithXpcDictionary:","@24@0:8@16",(id)response);
   receivedUV=uv;size_t n=0;const void *bytes=xpc_dictionary_get_data(response,"data",&n);replyBytesAvailable=bytes!=NULL;
   replyBytesEqual=[[NSData dataWithBytes:bytes length:n]isEqual:(NSData *)responsePointer];if(!receivedUV || !replyBytesEqual)errors++;
  }else errors++;
  dispatch_group_leave(group);
 }});xpc_release(message);
 long timed=dispatch_group_wait(group,dispatch_time(DISPATCH_TIME_NOW,3*NSEC_PER_SEC));__block NSData *record=nil;
 dispatch_sync(queue,^{
  BOOL accepted=!timed && !errors && audit && requests==1 && callbacks==1 && [decodedRequest isEqual:expected];
  NSDictionary *receipt=@{@"accepted":@(accepted),@"requests":@(requests),@"callbacks":@(callbacks),@"errorsBeforeCleanup":@(errors),@"peerSameProcess":@(audit),@"timedOut":@(timed!=0),@"request":decodedRequest?:@{},@"uvInitialized":@(receivedUV!=nil),@"replyBytesAvailable":@(replyBytesAvailable),@"replyBytesEqual":@(replyBytesEqual),@"requestBytes":@(request.length)};
  record=[[NSPropertyListSerialization dataWithPropertyList:receipt format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL]retain];
 });
 xpc_connection_cancel(client);if(peer)xpc_connection_cancel(peer);xpc_connection_cancel(listener);
 // Cancellation and process exit do not establish final OS resource settlement.
 *receiptPointer=record;return receivedUV;
}}
