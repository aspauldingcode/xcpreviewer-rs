// Reuse bounded owned-data inspection; no service connections are opened.
#define main property_list_probe_main
#include "xpc_probe.m"
#undef main

@interface NSObject (RawCoderProbe)
- (void)encodeObject:(id)value forKey:(NSString *)key;
- (id)decodeObjectOfClass:(Class)cls forKey:(NSString *)key;
@end

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        if (argc != 3 && argc != 4) return 2;
        NSString *mode = @(argv[1]), *requested = @(argv[2]);
        NSDictionary *classes = @{@"NSData":NSData.class,@"NSString":NSString.class,@"NSNumber":NSNumber.class,@"NSArray":NSArray.class,@"NSDictionary":NSDictionary.class,@"NSObject":NSObject.class};
        Class expected = classes[requested]; if (!expected) return 2;
        NSString *decodeKey=argc==4 ? @(argv[3]) : @"owned";
        if (![@[@"owned",@"alternate",@"data"] containsObject:decodeKey]) return 2;
        if (!dlopen("/System/Library/PrivateFrameworks/PreviewsServices.framework/PreviewsServices", RTLD_NOW|RTLD_LOCAL)) return 3;
        Class encoderClass=NSClassFromString(@"UVRawXPCCoder"), decoderClass=NSClassFromString(@"UVRawXPCDecoder");
        Method encoder=class_getInstanceMethod(encoderClass,@selector(encodeObject:forKey:));
        Method decoder=class_getInstanceMethod(decoderClass,@selector(decodeObjectOfClass:forKey:));
        Method initEncoder=class_getInstanceMethod(encoderClass,@selector(initWithXpcDictionary:));
        Method initDecoder=class_getInstanceMethod(decoderClass,@selector(initWithXpcDictionary:));
        if (!encoder || !decoder || !initEncoder || !initDecoder || strcmp(method_getTypeEncoding(encoder),"v32@0:8@16@24") || strcmp(method_getTypeEncoding(decoder),"@32@0:8#16@24") || strcmp(method_getTypeEncoding(initEncoder),"@24@0:8@16") || strcmp(method_getTypeEncoding(initDecoder),"@24@0:8@16")) return 4;
        NSDictionary *values=@{@"data":[NSData dataWithBytes:"owned\0bytes" length:11],@"empty-data":[NSData data],@"string":@"owned-text",@"number":@42,@"bool":@YES,@"array":@[@"owned",@7],@"dictionary":@{@"owned":@7}};
        if (!values[mode] && ![@[@"missing",@"wrong-wire-type",@"nil",@"overwrite"] containsObject:mode]) return 2;
        NSMutableDictionary *result=[@{@"mode":mode,@"requested_class":requested,@"decode_key":decodeKey,@"encoder_image":imageIdentity(encoder),@"scope":@"Owned raw coder objects only; no live IPC or handles"} mutableCopy];
        NSString *phase=@"encode";
        @try {
            xpc_object_t wire=xpc_dictionary_create(NULL,NULL,0);
            id enc=[[encoderClass alloc] initWithXpcDictionary:wire];
            if (![mode isEqual:@"missing"] && ![mode isEqual:@"wrong-wire-type"]) [enc encodeObject:values[mode] forKey:@"owned"];
            if ([mode isEqual:@"wrong-wire-type"]) xpc_dictionary_set_string(wire,"data","owned-wrong-type");
            if ([mode isEqual:@"overwrite"]) {
                [enc encodeObject:values[@"data"] forKey:@"first"];
                [enc encodeObject:[NSData dataWithBytes:"second" length:6] forKey:@"second"];
            }
            result[@"xpc_tree"]=describe(wire,0);phase=@"decode";
            id dec=[[decoderClass alloc] initWithXpcDictionary:wire];
            id value=[dec decodeObjectOfClass:expected forKey:decodeKey];
            result[@"outcome"]=value ? @"decoded" : @"nil";
            result[@"decoded_class"]=value ? NSStringFromClass([value class]) : @"";
            result[@"matches_requested_class"]=@((BOOL)(value && [value isKindOfClass:expected]));
            result[@"equals_original"]=@((BOOL)(value && [value isEqual:values[mode]]));
            if ([value isKindOfClass:NSData.class]) result[@"decoded_base64"]=[value base64EncodedStringWithOptions:0];
        } @catch (NSException *exception) {
            result[@"outcome"]=@"exception";result[@"phase"]=phase;result[@"name"]=exception.name;result[@"reason"]=exception.reason ?: @"";
        }
        NSData *json=[NSJSONSerialization dataWithJSONObject:result options:NSJSONWritingSortedKeys error:NULL];
        if (!json) return 7; fwrite(json.bytes,1,json.length,stdout);putchar('\n');return 0;
    }
}
