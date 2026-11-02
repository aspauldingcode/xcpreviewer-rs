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
 if(argc!=2)return 1;
 NSCAssert(dlopen("/System/Library/PrivateFrameworks/PreviewsServices.framework/Versions/A/PreviewsServices",RTLD_NOW|RTLD_LOCAL),@"Services load");Class cls=NSClassFromString(@"UVPropertyList");NSCAssert(cls,@"native class");
 NSMutableArray *rows=[NSMutableArray array];
 for(NSNumber *collision in @[@NO,@YES]){
  xpc_object_t destination=xpc_dictionary_create(NULL,NULL,0),heldDescriptor=NULL;__weak id weakValue=nil;BOOL sameDescriptor=NO;
  @autoreleasepool{
   int handles[2];NSCAssert(pipe(handles)==0,@"owned pipe");const char marker[]="owned-encoding";NSCAssert(write(handles[1],marker,sizeof(marker))==sizeof(marker),@"owned write");NSCAssert(close(handles[1])==0,@"writer close");
   xpc_object_t fd=xpc_fd_create(handles[0]);NSCAssert(fd,@"FD wrapper");NSCAssert(close(handles[0])==0,@"original reader close");
   const char *key=collision.boolValue?"data":"ownedDescriptor";xpc_dictionary_set_value(destination,key,fd);
   // Only the collision control keeps an explicit independent FD owner after
   // its data entry is overwritten. No native disposal policy is inferred.
   if(collision.boolValue)heldDescriptor=fd;
   id value=object([cls alloc],"initWithDictionary:",@{@"ownedRequest":@17});NSCAssert(value,@"UV init");weakValue=value;
   invoke(value,"encodeToXpcDictionary:","v24@0:8@16",destination);
   if(!collision.boolValue)sameDescriptor=xpc_dictionary_get_value(destination,"ownedDescriptor")==fd;
  }
  NSCAssert(weakValue==nil,@"UV object should leave owned pool");
  xpc_object_t data=xpc_dictionary_get_value(destination,"data");NSCAssert(data&&xpc_get_type(data)==XPC_TYPE_DATA,@"data replacement");
  size_t length=0;const void *bytes=xpc_dictionary_get_data(destination,"data",&length);NSCAssert(bytes&&length>0,@"serialized bytes");
  NSDictionary *decoded=[NSPropertyListSerialization propertyListWithData:[NSData dataWithBytes:bytes length:length] options:0 format:NULL error:NULL];NSCAssert([decoded isEqual:@{@"ownedRequest":@17}],@"complete payload");
  xpc_object_t remaining=collision.boolValue?heldDescriptor:xpc_dictionary_get_value(destination,"ownedDescriptor");NSCAssert(remaining&&xpc_get_type(remaining)==XPC_TYPE_FD,@"remaining FD");
  int duplicate=xpc_fd_dup(remaining);NSCAssert(duplicate>=0,@"post-pool duplication");char readback[64]={0};ssize_t n=read(duplicate,readback,sizeof(readback));NSCAssert(close(duplicate)==0,@"duplicate close");const char marker[]="owned-encoding";NSCAssert(n==sizeof(marker)&&!memcmp(readback,marker,sizeof(marker)),@"complete FD readback");
  [rows addObject:@{@"case":collision.boolValue?@"replace-data-fd":@"preserve-extra-fd",@"uvWeakCleared":@(weakValue==nil),@"dataIsData":@YES,@"decoded":decoded,@"extraFDIdentityPreserved":@(sameDescriptor),@"rootEntryCount":@(xpc_dictionary_get_count(destination)),@"fdReadbackBytes":@(n),@"fdReadbackMatches":@YES,@"independentCollisionFDOwner":collision}];
 }
 NSData *result=[NSPropertyListSerialization dataWithPropertyList:rows format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL];NSCAssert([result writeToFile:@(argv[1]) atomically:YES],@"owned receipt write");puts("two owned descriptor encode controls passed");
}}
