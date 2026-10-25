#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#include <xpc/xpc.h>
#include <dlfcn.h>
static NSInvocation *call(id target,const char *name,const char *encoding,id argument) {
    SEL selector=sel_registerName(name);Method method=class_getInstanceMethod([target class],selector);
    if(!method || strcmp(method_getTypeEncoding(method),encoding)!=0){fprintf(stderr,"signature mismatch: %s\n",name);exit(4);}
    NSInvocation *inv=[NSInvocation invocationWithMethodSignature:[target methodSignatureForSelector:selector]];
    [inv setTarget:target];[inv setSelector:selector];
    if([inv.methodSignature numberOfArguments]==3)[inv setArgument:&argument atIndex:2];
    [inv invoke];return inv;
}
static id objectCall(id target,const char *name,const char *encoding,id argument) {id result=nil;[call(target,name,encoding,argument) getReturnValue:&result];return result;}
static id initialize(Class cls,id wire) {return objectCall([cls alloc],"initWithXpcDictionary:","@24@0:8@16",wire);}
int main(int argc,const char **argv) {@autoreleasepool {
    if(argc!=3)return 1;
    const char *image="/System/Library/PrivateFrameworks/PreviewsServices.framework/Versions/A/PreviewsServices";
    if(!dlopen(image,RTLD_NOW|RTLD_LOCAL))return 2;Class cls=NSClassFromString(@"UVPropertyList");if(!cls)return 3;
    NSString *input=[NSString stringWithUTF8String:argv[1]],*output=[NSString stringWithUTF8String:argv[2]];
    NSArray *names=@[@"normal",@"error",@"empty",@"malformed"];NSMutableDictionary *responses=[NSMutableDictionary dictionary];
    for(NSString *name in names){NSData *data=[NSData dataWithContentsOfFile:[input stringByAppendingPathComponent:[name stringByAppendingString:@".data"]]];if(!data)return 5;responses[name]=data;}
    NSData *request=[NSData dataWithContentsOfFile:[input stringByAppendingPathComponent:@"request.data"]];if(!request)return 6;
    NSDictionary *expectedRequest=[NSPropertyListSerialization propertyListWithData:request options:0 format:NULL error:NULL];if(!expectedRequest)return 7;
    dispatch_queue_t queue=dispatch_queue_create("owned.encoded.response",DISPATCH_QUEUE_SERIAL);dispatch_group_t group=dispatch_group_create();
    for(__unused NSString *name in names)dispatch_group_enter(group);
    __block xpc_connection_t peer=NULL;__block int requests=0,capabilities=0,errors=0;
    NSMutableArray *rows=[NSMutableArray array];
    xpc_connection_t listener=xpc_connection_create(NULL,queue);if(!listener)return 8;
    xpc_connection_set_event_handler(listener,^(xpc_object_t incoming){@autoreleasepool {
        if(xpc_get_type(incoming)!=XPC_TYPE_CONNECTION){errors++;return;}
        peer=(xpc_connection_t)incoming;xpc_retain(peer);
        xpc_connection_set_event_handler(peer,^(xpc_object_t message){@autoreleasepool {@try {
            if(xpc_get_type(message)!=XPC_TYPE_DICTIONARY){errors++;return;}
            const char *raw=xpc_dictionary_get_string(message,"owned.case");if(!raw){errors++;return;}NSString *name=[NSString stringWithUTF8String:raw];NSData *data=responses[name];if(!data){errors++;return;}
            id plist=initialize(cls,(id)message);NSDictionary *decoded=plist?objectCall(plist,"dictionary","@16@0:8",nil):nil;
            if(![decoded isEqual:expectedRequest])errors++;[plist release];requests++;
            xpc_object_t reply=xpc_dictionary_create_reply(message);if(!reply){errors++;return;}capabilities++;
            xpc_dictionary_set_string(reply,"owned.case",raw);xpc_dictionary_set_data(reply,"data",data.bytes,data.length);
            xpc_connection_send_message(peer,reply);xpc_release(reply);
        }@catch(NSException *e){errors++;fprintf(stderr,"owned server exception: %s\n",e.name.UTF8String);}}});
        xpc_connection_activate(peer);
    }});
    xpc_connection_activate(listener);xpc_endpoint_t endpoint=xpc_endpoint_create(listener);if(!endpoint)return 9;
    xpc_connection_t client=xpc_connection_create_from_endpoint(endpoint);xpc_release(endpoint);if(!client)return 10;
    xpc_connection_set_event_handler(client,^(xpc_object_t event){if(xpc_get_type(event)==XPC_TYPE_ERROR)errors++;});xpc_connection_activate(client);
    for(NSString *name in names){xpc_object_t message=xpc_dictionary_create(NULL,NULL,0);xpc_dictionary_set_string(message,"owned.case",name.UTF8String);xpc_dictionary_set_data(message,"data",request.bytes,request.length);
        xpc_connection_send_message_with_reply(client,message,queue,^(xpc_object_t reply){@autoreleasepool {@try {
            if(xpc_get_type(reply)!=XPC_TYPE_DICTIONARY){errors++;[rows addObject:@{@"name":name,@"dictionary":@NO}];dispatch_group_leave(group);return;}
            size_t length=0;const void *bytes=xpc_dictionary_get_data(reply,"data",&length);NSData *wire=[NSData dataWithBytes:bytes length:length];NSData *expected=responses[name];BOOL same=[wire isEqual:expected];
            [wire writeToFile:[output stringByAppendingPathComponent:[name stringByAppendingString:@".wire-data"]] atomically:YES];
            id plist=initialize(cls,(id)reply);NSDictionary *decoded=plist?objectCall(plist,"dictionary","@16@0:8",nil):nil;
            NSDictionary *expectedDictionary=(([name isEqual:@"empty"]||[name isEqual:@"malformed"])?@{}:[NSPropertyListSerialization propertyListWithData:expected options:0 format:NULL error:NULL]);
            BOOL matches=[decoded isEqual:expectedDictionary];BOOL copied=YES,extra=YES;BOOL echoAvailable=NO;BOOL echoInitialized=NO;
            if(plist){xpc_object_t echo=xpc_dictionary_create(NULL,NULL,0);xpc_dictionary_set_int64(echo,"owned.extra",17);call(plist,"encodeToXpcDictionary:","v24@0:8@16",(id)echo);size_t count=0;const void *p=xpc_dictionary_get_data(echo,"data",&count);copied=[[NSData dataWithBytes:p length:count]isEqual:expected];extra=xpc_dictionary_get_int64(echo,"owned.extra")==17;echoAvailable=p!=NULL;id echoPlist=initialize(cls,(id)echo);echoInitialized=echoPlist!=nil;[echoPlist release];xpc_release(echo);}
            if(decoded){NSData *normalized=[NSPropertyListSerialization dataWithPropertyList:decoded format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL];[normalized writeToFile:[output stringByAppendingPathComponent:[name stringByAppendingString:@".decoded"]] atomically:YES];}
            BOOL present=xpc_get_type(xpc_dictionary_get_value(reply,"data"))==XPC_TYPE_DATA;
            if(!same||!matches||!copied||!extra||!present)errors++;
            [rows addObject:@{@"name":name,@"dictionary":@YES,@"data_present":@(present),@"bytes":@(length),@"data_bytes_available":@(bytes!=NULL),@"echo_bytes_available":@(echoAvailable),@"echo_uv_initialized":@(echoInitialized),@"wire_equal":@(same),@"uv_initialized":@(plist!=nil),@"decoded_matches":@(matches),@"uv_reencoded_equal":@(copied),@"extra_preserved":@(extra),@"xpc_count":@(xpc_dictionary_get_count(reply))}];[plist release];
        }@catch(NSException *e){errors++;[rows addObject:@{@"name":name,@"exception":e.name}];}dispatch_group_leave(group);}});xpc_release(message);
    }
    long timed=dispatch_group_wait(group,dispatch_time(DISPATCH_TIME_NOW,3*NSEC_PER_SEC));__block int failed=1;
    dispatch_sync(queue,^{
        failed=timed||errors||requests!=4||capabilities!=4||rows.count!=4;
        NSArray *sorted=[rows sortedArrayUsingDescriptors:@[[NSSortDescriptor sortDescriptorWithKey:@"name" ascending:YES]]];
        NSDictionary *record=@{@"class_image":[NSString stringWithUTF8String:class_getImageName(cls)],@"requests":@(requests),@"capabilities":@(capabilities),@"callbacks":@(rows.count),@"errors_before_cleanup":@(errors),@"timed_out":@(timed!=0),@"rows":sorted};NSData *json=[NSJSONSerialization dataWithJSONObject:record options:NSJSONWritingSortedKeys error:NULL];fwrite(json.bytes,1,json.length,stdout);putchar('\n');
    });
    xpc_connection_cancel(client);if(peer)xpc_connection_cancel(peer);xpc_connection_cancel(listener);
    // Only owned connections are canceled; return/exit is not rights settlement.
    return failed?11:0;
}}
