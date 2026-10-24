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
    NSDictionary *nested=@{@"bytes":[NSData dataWithBytes:bytes length:128],@"name":@"owned/🪨",@"min":@(LLONG_MIN),@"max":@(LLONG_MAX),@"real":@3.5,@"date":[NSDate dateWithTimeIntervalSinceReferenceDate:17],@"array":@[@YES,@"value"]};
    NSDictionary *error=@{@"domain":@"owned/error",@"code":@-17,@"userInfo":@{@"incompatible":[[[NSObject alloc]init]autorelease],NSLocalizedDescriptionKey:@"owned failure"}};
    NSArray *cases=@[@[@"empty",@{}],@[@"nested",nested],@[@"invalid_error",error]];
    NSMutableArray *results=[NSMutableArray array];NSString *folder=[NSString stringWithUTF8String:argv[1]];
    for(NSArray *entry in cases){@try{
        NSString *name=entry[0];NSDictionary *input=entry[1];id plist=initialize(cls,"initWithDictionary:",input);
        NSData *data=objectCall(plist,"data","@16@0:8",nil);
        [data writeToFile:[folder stringByAppendingPathComponent:[name stringByAppendingString:@".data"]] atomically:YES];
        xpc_object_t wire=xpc_dictionary_create(NULL,NULL,0);call(plist,"encodeToXpcDictionary:","v24@0:8@16",(id)wire);
        size_t nativeLength=0;const void *nativeData=xpc_dictionary_get_data(wire,"data",&nativeLength);[[NSData dataWithBytes:nativeData length:nativeLength] writeToFile:[folder stringByAppendingPathComponent:[name stringByAppendingString:@".wire-data"]] atomically:YES];
        NSMutableArray *keys=[NSMutableArray array];__block BOOL allData=YES;__block BOOL dataEqual=YES;
        xpc_dictionary_apply(wire,^bool(const char *key,xpc_object_t value){
            [keys addObject:[NSString stringWithUTF8String:key]];BOOL isData=xpc_get_type(value)==XPC_TYPE_DATA;allData=allData&&isData;
            if(isData){NSData *payload=[NSData dataWithBytes:xpc_data_get_bytes_ptr(value) length:xpc_data_get_length(value)];dataEqual=dataEqual&&[payload isEqual:data];}
            else dataEqual=NO;return true;
        });
        id restored=initialize(cls,"initWithXpcDictionary:",(id)wire);NSDictionary *decoded=restored?objectCall(restored,"dictionary","@16@0:8",nil):nil;
        if(decoded){NSData *normalized=[NSPropertyListSerialization dataWithPropertyList:decoded format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL];[normalized writeToFile:[folder stringByAppendingPathComponent:[name stringByAppendingString:@".decoded"]] atomically:YES];}
        [results addObject:@{@"name":name,@"data_bytes":@(data.length),@"xpc_count":@(xpc_dictionary_get_count(wire)),@"keys":keys,@"all_data":@(allData),@"payload_matches_data":@(dataEqual),@"restored":@(restored!=nil),@"decoded_count":@(decoded.count),@"matches_input":@([input isEqual:decoded])}];
        [restored release];xpc_release(wire);
        xpc_object_t occupied=xpc_dictionary_create(NULL,NULL,0);xpc_dictionary_set_int64(occupied,"owned.extra",17);xpc_dictionary_set_string(occupied,"data","old");
        call(plist,"encodeToXpcDictionary:","v24@0:8@16",(id)occupied);
        [results addObject:@{@"name":[name stringByAppendingString:@"_overwrite"],@"xpc_count":@(xpc_dictionary_get_count(occupied)),@"extra":@(xpc_dictionary_get_int64(occupied,"owned.extra")),@"data_type":@(xpc_get_type(xpc_dictionary_get_value(occupied,"data"))==XPC_TYPE_DATA)}];
        xpc_release(occupied);[plist release];
    }@catch(NSException *exception){[results addObject:@{@"name":entry[0],@"exception":exception.name,@"reason":exception.reason?:@""}];}}
    for(NSString *name in @[@"missing",@"wrong_type",@"empty_data",@"malformed",@"array_root",@"xml"]){@try{
        xpc_object_t wire=xpc_dictionary_create(NULL,NULL,0);
        if([name isEqual:@"wrong_type"])xpc_dictionary_set_string(wire,"data","owned");
        if([name isEqual:@"empty_data"])xpc_dictionary_set_data(wire,"data",NULL,0);
        NSData *inputData=nil;
        if([name isEqual:@"malformed"])inputData=[@"owned invalid plist" dataUsingEncoding:NSUTF8StringEncoding];
        if([name isEqual:@"array_root"])inputData=[NSPropertyListSerialization dataWithPropertyList:@[@"owned"] format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL];
        if([name isEqual:@"xml"])inputData=[NSPropertyListSerialization dataWithPropertyList:@{@"owned":@17} format:NSPropertyListXMLFormat_v1_0 options:0 error:NULL];
        if(inputData){xpc_dictionary_set_data(wire,"data",inputData.bytes,inputData.length);[inputData writeToFile:[folder stringByAppendingPathComponent:[name stringByAppendingString:@".wire-data"]] atomically:YES];}
        id restored=initialize(cls,"initWithXpcDictionary:",(id)wire);NSDictionary *decoded=restored?objectCall(restored,"dictionary","@16@0:8",nil):nil;
        if(decoded){NSData *normalized=[NSPropertyListSerialization dataWithPropertyList:decoded format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL];[normalized writeToFile:[folder stringByAppendingPathComponent:[name stringByAppendingString:@".decoded"]] atomically:YES];}
        [results addObject:@{@"name":name,@"restored":@(restored!=nil),@"decoded_count":@(decoded.count)}];[restored release];xpc_release(wire);
    }@catch(NSException *exception){[results addObject:@{@"name":name,@"exception":exception.name,@"reason":exception.reason?:@""}];}}
    xpc_object_t copiedWire=xpc_dictionary_create(NULL,NULL,0);
    @autoreleasepool {
        NSMutableData *source=[NSMutableData dataWithData:[NSPropertyListSerialization dataWithPropertyList:nested format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL]];
        NSData *before=[NSData dataWithData:source];id plist=initialize(cls,"initWithData:",source);
        call(plist,"encodeToXpcDictionary:","v24@0:8@16",(id)copiedWire);
        memset(source.mutableBytes,0xff,source.length);
        NSData *after=objectCall(plist,"data","@16@0:8",nil);
        size_t length=0;const void *payload=xpc_dictionary_get_data(copiedWire,"data",&length);
        NSData *wireData=[NSData dataWithBytes:payload length:length];
        [results addObject:@{@"name":@"mutable_data_copy",@"stored_data_follows_mutation":@([after isEqual:source]),@"wire_keeps_pre_mutation_bytes":@([wireData isEqual:before]),@"wire_differs_from_mutated_source":@(![wireData isEqual:source]),@"xpc_count":@(xpc_dictionary_get_count(copiedWire))}];
        [plist release];
    }
    id afterPool=initialize(cls,"initWithXpcDictionary:",(id)copiedWire);NSDictionary *copiedDictionary=objectCall(afterPool,"dictionary","@16@0:8",nil);
    [results addObject:@{@"name":@"copy_after_source_pool_exit",@"restored":@(afterPool!=nil),@"matches_input":@([copiedDictionary isEqual:nested])}];
    [afterPool release];xpc_release(copiedWire);
    NSData *json=[NSJSONSerialization dataWithJSONObject:results options:NSJSONWritingPrettyPrinted|NSJSONWritingSortedKeys error:NULL];fwrite(json.bytes,1,json.length,stdout);putchar('\n');return 0;
}}
