#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#include <xpc/xpc.h>
#include <dlfcn.h>
static NSInvocation *call(id target,const char *name,const char *encoding,id argument) {
    SEL selector=sel_registerName(name);Method method=class_getInstanceMethod([target class],selector);
    if(!method || strcmp(method_getTypeEncoding(method),encoding)!=0){fprintf(stderr,"signature mismatch: %s\n",name);exit(4);}
    NSInvocation *invocation=[NSInvocation invocationWithMethodSignature:[target methodSignatureForSelector:selector]];
    [invocation setTarget:target];[invocation setSelector:selector];
    if([invocation.methodSignature numberOfArguments]==3)[invocation setArgument:&argument atIndex:2];
    [invocation invoke];return invocation;
}
static id objectCall(id target,const char *name,const char *encoding,id argument) {
    id result=nil;[call(target,name,encoding,argument) getReturnValue:&result];return result;
}
static id initialize(Class cls,const char *name,id argument) {return objectCall([cls alloc],name,"@24@0:8@16",argument);}
int main(int argc,const char **argv){@autoreleasepool {
    if(argc!=2)return 1;
    if(!dlopen("/System/Library/PrivateFrameworks/PreviewsServices.framework/Versions/A/PreviewsServices",RTLD_NOW|RTLD_LOCAL))return 2;
    Class cls=NSClassFromString(@"UVPropertyList");if(!cls)return 3;
    unsigned char bytes[128];for(unsigned i=0;i<128;i++)bytes[i]=i;
    NSDictionary *fields=@{@"domain":@"owned/reply/🪨",@"code":@(LLONG_MIN),@"userInfo":@{@"bytes":[NSData dataWithBytes:bytes length:128],@"reason":@"owned failure"}};
    id message=initialize(cls,"initWithDictionary:",fields);xpc_object_t wire=xpc_dictionary_create(NULL,NULL,0);
    call(message,"encodeToXpcDictionary:","v24@0:8@16",(id)wire);[message release];
    size_t length=0;const void *buffer=xpc_dictionary_get_data(wire,"data",&length);
    NSData *data=[NSData dataWithBytes:buffer length:length];if(![data writeToFile:[NSString stringWithUTF8String:argv[1]] atomically:YES])return 5;
    id received=initialize(cls,"initWithXpcDictionary:",(id)wire);NSDictionary *decoded=objectCall(received,"dictionary","@16@0:8",nil);
    NSData *saved=objectCall(received,"data","@16@0:8",nil);
    NSDictionary *record=@{@"class_image":[NSString stringWithUTF8String:class_getImageName(cls)],@"xpc_count":@(xpc_dictionary_get_count(wire)),@"bytes":@(length),@"restored":@(received!=nil),@"complete_fields_match":@([decoded isEqual:fields]),@"serialized_bytes_preserved":@([saved isEqual:data])};
    NSData *json=[NSJSONSerialization dataWithJSONObject:record options:NSJSONWritingPrettyPrinted|NSJSONWritingSortedKeys error:NULL];fwrite(json.bytes,1,json.length,stdout);putchar('\n');
    [received release];xpc_release(wire);return 0;
}}
