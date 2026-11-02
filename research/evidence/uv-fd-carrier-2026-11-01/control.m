#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#include <xpc/xpc.h>
#include <dlfcn.h>
#include <mach-o/loader.h>
#include <unistd.h>
#include <string.h>
static NSString *profile(IMP implementation) {
 Dl_info info={0};NSCAssert(dladdr((void*)implementation,&info),@"implementation identity");
 NSCAssert(!strcmp(info.dli_fname,"/System/Library/PrivateFrameworks/PreviewsServices.framework/Versions/A/PreviewsServices"),@"implementation image");
 const struct mach_header_64 *h=info.dli_fbase;const struct load_command *lc=(const void*)(h+1);NSString *uuid=nil;
 for(uint32_t i=0;i<h->ncmds;i++){if(lc->cmd==LC_UUID){const struct uuid_command *u=(const void*)lc;NSMutableString *s=[NSMutableString string];for(unsigned j=0;j<16;j++)[s appendFormat:@"%02x",u->uuid[j]];uuid=s;}lc=(const void*)((const char*)lc+lc->cmdsize);}
 NSCAssert([uuid isEqual:@"fffb683f59433c2591b272d6e5174fa3"],@"unsupported Services UUID");return uuid;
}
static NSInvocation *invoke(id target,const char *name,const char *encoding,id argument) {
 SEL selector=sel_registerName(name);Method method=class_getInstanceMethod([target class],selector);
 NSCAssert(method&&!strcmp(method_getTypeEncoding(method),encoding),@"method signature");profile(method_getImplementation(method));
 NSInvocation *call=[NSInvocation invocationWithMethodSignature:[target methodSignatureForSelector:selector]];call.target=target;call.selector=selector;
 if(call.methodSignature.numberOfArguments==3)[call setArgument:&argument atIndex:2];[call invoke];return call;
}
static id object(id target,const char *name,id argument){__unsafe_unretained id value=nil;[invoke(target,name,"@24@0:8@16",argument) getReturnValue:&value];return value;}
int main(int argc,const char **argv){@autoreleasepool{
 if(argc!=3)return 1;BOOL collision=!strcmp(argv[1],"collision");
 NSCAssert(dlopen("/System/Library/PrivateFrameworks/PreviewsServices.framework/Versions/A/PreviewsServices",RTLD_NOW|RTLD_LOCAL),@"Services load");Class cls=NSClassFromString(@"UVPropertyList");NSCAssert(cls,@"native class");
 dispatch_queue_t queue=dispatch_queue_create("owned.uv.fd.carrier",DISPATCH_QUEUE_SERIAL);
 dispatch_semaphore_t arrived=dispatch_semaphore_create(0),released=dispatch_semaphore_create(0),finished=dispatch_semaphore_create(0);
 __block xpc_connection_t remote=nil;__block NSDictionary *receipt=nil;__block unsigned connections=0,messages=0;
 xpc_connection_t listener=xpc_connection_create(NULL,queue);NSCAssert(listener,@"listener");
 xpc_connection_set_event_handler(listener,^(xpc_object_t event){
  if(xpc_get_type(event)!=XPC_TYPE_CONNECTION)return;
  remote=event;connections++;
  xpc_connection_set_event_handler(remote,^(xpc_object_t message){
   if(xpc_get_type(message)!=XPC_TYPE_DICTIONARY)return;
   @autoreleasepool{
    messages++;BOOL sameProcess=xpc_connection_get_pid(remote)==getpid();dispatch_semaphore_signal(arrived);
    NSCAssert(dispatch_semaphore_wait(released,dispatch_time(DISPATCH_TIME_NOW,3*NSEC_PER_SEC))==0,@"sender release gate");
    id projected=object([cls alloc],"initWithXpcDictionary:",message);NSCAssert(projected,@"received UV init");
    __unsafe_unretained id decoded=nil;[invoke(projected,"dictionary","@16@0:8",nil) getReturnValue:&decoded];NSCAssert([decoded isEqual:@{@"ownedRequest":@17}],@"complete received native projection");
    xpc_object_t fd=xpc_dictionary_get_value(message,"ownedDescriptor");ssize_t count=0;BOOL readMatches=NO;
    if(!collision){NSCAssert(fd&&xpc_get_type(fd)==XPC_TYPE_FD,@"received FD type");int duplicate=xpc_fd_dup(fd);NSCAssert(duplicate>=0,@"received FD duplicate");char data[64]={0};count=read(duplicate,data,sizeof(data));NSCAssert(close(duplicate)==0,@"received duplicate close");const char marker[]="owned-carrier";readMatches=count==sizeof(marker)&&!memcmp(data,marker,sizeof(marker));NSCAssert(readMatches,@"received FD bytes");}
    else NSCAssert(!fd,@"collision descriptor not forwarded as extra field");
    receipt=@{@"case":collision?@"collision":@"extra-fd",@"sameProcessPeer":@(sameProcess),@"nativeProjection":decoded,@"receivedRootCount":@(xpc_dictionary_get_count(message)),@"descriptorPresent":@(fd!=NULL),@"readbackBytes":@(count),@"readbackMatches":@(readMatches),@"senderReleaseGatePassed":@YES};
   }
   dispatch_semaphore_signal(finished);
  });xpc_connection_activate(remote);
 });xpc_connection_activate(listener);
 xpc_endpoint_t endpoint=xpc_endpoint_create(listener);xpc_connection_t client=xpc_connection_create_from_endpoint(endpoint);NSCAssert(client,@"client");xpc_connection_set_event_handler(client,^(xpc_object_t event){});xpc_connection_activate(client);
 __weak id weakSource=nil;
 @autoreleasepool{
  int handles[2];NSCAssert(pipe(handles)==0,@"owned pipe");const char marker[]="owned-carrier";NSCAssert(write(handles[1],marker,sizeof(marker))==sizeof(marker),@"owned pipe write");NSCAssert(close(handles[1])==0,@"writer close");
  xpc_object_t descriptor=xpc_fd_create(handles[0]);NSCAssert(descriptor,@"FD wrapper");NSCAssert(close(handles[0])==0,@"original reader close");
  xpc_object_t envelope=xpc_dictionary_create(NULL,NULL,0);xpc_dictionary_set_value(envelope,collision?"data":"ownedDescriptor",descriptor);
  id source=object([cls alloc],"initWithDictionary:",@{@"ownedRequest":@17});weakSource=source;invoke(source,"encodeToXpcDictionary:","v24@0:8@16",envelope);
  xpc_connection_send_message(client,envelope);
  NSCAssert(dispatch_semaphore_wait(arrived,dispatch_time(DISPATCH_TIME_NOW,3*NSEC_PER_SEC))==0,@"owned receive deadline");
 }
 NSCAssert(weakSource==nil,@"sender UV weak cleared");dispatch_semaphore_signal(released);
 NSCAssert(dispatch_semaphore_wait(finished,dispatch_time(DISPATCH_TIME_NOW,3*NSEC_PER_SEC))==0,@"owned projection deadline");
 __block NSDictionary *snapshot;dispatch_sync(queue,^{NSMutableDictionary *out=[receipt mutableCopy];out[@"connections"]=@(connections);out[@"messages"]=@(messages);out[@"senderUVWeakCleared"]=@(weakSource==nil);snapshot=out;});
 xpc_connection_cancel(client);if(remote)xpc_connection_cancel(remote);xpc_connection_cancel(listener);
 NSData *data=[NSPropertyListSerialization dataWithPropertyList:snapshot format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL];NSCAssert([data writeToFile:@(argv[2]) atomically:YES],@"owned result");puts("owned native UV/FD carrier passed");
}}
