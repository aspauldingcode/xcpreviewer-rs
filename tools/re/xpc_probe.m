// Owned synthetic dictionaries only. No XPC connection or Mach port is created.
#import <Foundation/Foundation.h>
#import <xpc/xpc.h>
#import <objc/runtime.h>
#import <dlfcn.h>
#import <mach-o/dyld.h>
#import <mach-o/loader.h>

@interface NSObject (PreviewXPC)
- (id)initWithDictionary:(NSDictionary *)dictionary;
- (id)initWithXpcDictionary:(xpc_object_t)dictionary;
- (void)encodeToXpcDictionary:(xpc_object_t)dictionary;
- (NSDictionary *)dictionary;
- (NSData *)data;
- (id)initWithData:(NSData *)data;
@end

static NSDictionary *imageIdentity(Method method) {
    Dl_info info = {0};
    if (!dladdr((const void *)method_getImplementation(method), &info) || !info.dli_fbase) return @{};
    const struct mach_header_64 *header = info.dli_fbase;
    if (header->magic != MH_MAGIC_64) return @{};
    const uint8_t *cursor = (const uint8_t *)(header + 1), *end = cursor + header->sizeofcmds;
    for (uint32_t i = 0; i < header->ncmds && i < 4096; i++) {
        if (cursor + sizeof(struct load_command) > end) break;
        const struct load_command *command = (const struct load_command *)cursor;
        if (command->cmdsize < sizeof(*command) || cursor + command->cmdsize > end) break;
        if (command->cmd == LC_UUID && command->cmdsize >= sizeof(struct uuid_command)) {
            NSString *uuid = [[[NSUUID alloc] initWithUUIDBytes:((const struct uuid_command *)command)->uuid] UUIDString];
            return @{@"path": @(info.dli_fname), @"uuid": uuid};
        }
        cursor += command->cmdsize;
    }
    return @{};
}

static id describe(xpc_object_t object, unsigned depth) {
    if (depth > 12) return @{@"type": @"unresolved", @"reason": @"depth limit"};
    xpc_type_t type = xpc_get_type(object);
    if (type == XPC_TYPE_DICTIONARY) {
        NSMutableDictionary *items = [NSMutableDictionary dictionary];
        __block NSUInteger count = 0;
        xpc_dictionary_apply(object, ^bool(const char *key, xpc_object_t value) {
            if (++count > 128) return false;
            items[@(key)] = describe(value, depth + 1); return true;
        });
        return @{@"type": @"dictionary", @"count": @(xpc_dictionary_get_count(object)), @"items": items};
    }
    if (type == XPC_TYPE_ARRAY) {
        NSMutableArray *items = [NSMutableArray array];
        size_t count = xpc_array_get_count(object);
        for (size_t i = 0; i < MIN(count, 128); i++) [items addObject:describe(xpc_array_get_value(object, i), depth + 1)];
        return @{@"type": @"array", @"count": @(count), @"items": items};
    }
    if (type == XPC_TYPE_DATA) {
        size_t size = xpc_data_get_length(object);
        if (size > 1024 * 1024) return @{@"type": @"data", @"bytes": @(size), @"truncated": @YES};
        NSData *data = [NSData dataWithBytes:xpc_data_get_bytes_ptr(object) length:size];
        return @{@"type": @"data", @"bytes": @(size), @"base64": [data base64EncodedStringWithOptions:0]};
    }
    if (type == XPC_TYPE_STRING) return @{@"type": @"string", @"value": @(xpc_string_get_string_ptr(object))};
    if (type == XPC_TYPE_INT64) return @{@"type": @"int64", @"value": @(xpc_int64_get_value(object))};
    if (type == XPC_TYPE_UINT64) return @{@"type": @"uint64", @"value": @(xpc_uint64_get_value(object))};
    if (type == XPC_TYPE_DOUBLE) {
        double value = xpc_double_get_value(object); uint64_t bits; memcpy(&bits, &value, sizeof(bits));
        return @{@"type": @"double", @"bits_hex": [NSString stringWithFormat:@"%016llx", (unsigned long long)bits]};
    }
    if (type == XPC_TYPE_BOOL) return @{@"type": @"bool", @"value": @(xpc_bool_get_value(object))};
    if (type == XPC_TYPE_DATE) return @{@"type": @"date", @"nanoseconds": @(xpc_date_get_value(object))};
    if (type == XPC_TYPE_NULL) return @{@"type": @"null"};
    return @{@"type": @"unresolved", @"reason": @"resource or unsupported XPC type; not serialized as bytes"};
}

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        if (argc < 2 || argc > 3) return 2;
        NSString *mode = argc == 3 ? @(argv[2]) : @"roundtrip";
        BOOL directMode = [mode hasPrefix:@"direct-prefix-"];
        BOOL prefixMode = [mode hasPrefix:@"prefix-"] || directMode;
        unsigned long long prefix = 0;
        if (prefixMode) {
            const char *number = [mode substringFromIndex:directMode ? 14 : 7].UTF8String;
            if (!number[0] || strlen(number) > 5 || strspn(number, "0123456789") != strlen(number)) return 2;
            prefix = strtoull(number, NULL, 10); if (prefix > 65536) return 2;
        } else if (![@[@"roundtrip", @"missing-data", @"wrong-type", @"truncated-data", @"extra-key"] containsObject:mode]) return 2;
        if (!dlopen("/System/Library/PrivateFrameworks/PreviewsServices.framework/PreviewsServices", RTLD_NOW | RTLD_LOCAL)) return 3;
        Class cls = NSClassFromString(@"UVPropertyList");
        Method encoder = class_getInstanceMethod(cls, @selector(encodeToXpcDictionary:));
        Method decoder = class_getInstanceMethod(cls, @selector(initWithXpcDictionary:));
        Method directDecoder = class_getInstanceMethod(cls, @selector(initWithData:));
        if (!encoder || !decoder || strcmp(method_getTypeEncoding(encoder), "v24@0:8@16") || strcmp(method_getTypeEncoding(decoder), "@24@0:8@16")) return 4;
        if (directMode && (!directDecoder || strcmp(method_getTypeEncoding(directDecoder), "@24@0:8@16"))) return 4;
        NSData *fixture = [NSData dataWithContentsOfFile:@(argv[1])];
        id input = [NSPropertyListSerialization propertyListWithData:fixture options:NSPropertyListImmutable format:NULL error:NULL];
        if (![input isKindOfClass:NSDictionary.class]) return 5;
        @try {
            id original = [[cls alloc] initWithDictionary:input];
            xpc_object_t wire = xpc_dictionary_create(NULL, NULL, 0);
            [original encodeToXpcDictionary:wire];
            NSData *originalData = [original data];
            if ([mode isEqual:@"missing-data"]) xpc_dictionary_set_value(wire, "data", NULL);
            if ([mode isEqual:@"wrong-type"]) xpc_dictionary_set_string(wire, "data", "owned-invalid-type");
            if ([mode isEqual:@"truncated-data"]) xpc_dictionary_set_data(wire, "data", originalData.bytes, MIN(originalData.length, 8));
            if (prefixMode) xpc_dictionary_set_data(wire, "data", originalData.bytes, MIN(originalData.length, prefix));
            if ([mode isEqual:@"extra-key"]) xpc_dictionary_set_string(wire, "owned_extra", "owned-extra-value");
            id object = directMode ? [[cls alloc] initWithData:[originalData subdataWithRange:NSMakeRange(0, MIN(originalData.length, prefix))]] : [[cls alloc] initWithXpcDictionary:wire];
            id decoded = [object dictionary];
            NSData *replay = decoded ? [NSPropertyListSerialization dataWithPropertyList:decoded format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL] : nil;
            NSDictionary *result = @{@"xpc_tree": describe(wire, 0), @"round_trip_equal": @([input isEqual:decoded]),
                @"decoded_base64": replay ? [replay base64EncodedStringWithOptions:0] : @"",
                @"uv_data_base64": [originalData base64EncodedStringWithOptions:0],
                @"decoded_empty_dictionary": @((BOOL)([decoded isKindOfClass:NSDictionary.class] && [decoded count] == 0)),
                @"outcome": decoded ? @"decoded" : @"nil", @"mode": mode, @"encoder_image": imageIdentity(encoder),
                @"decoder_kind": directMode ? @"initWithData:" : @"initWithXpcDictionary:",
                @"encoder_encoding": @(method_getTypeEncoding(encoder)), @"decoder_encoding": @(method_getTypeEncoding(decoder)),
                @"scope": @"Owned synthetic XPC object; no service connection, captured traffic or resource transfer"};
            NSData *json = [NSJSONSerialization dataWithJSONObject:result options:NSJSONWritingSortedKeys error:NULL];
            if (!json) return 7;
            fwrite(json.bytes, 1, json.length, stdout); putchar('\n');
            return ![mode isEqual:@"roundtrip"] || [input isEqual:decoded] ? 0 : 8;
        } @catch (NSException *exception) {
            NSDictionary *result = @{@"outcome": @"exception", @"name": exception.name, @"reason": exception.reason ?: @"", @"mode": mode};
            NSData *json = [NSJSONSerialization dataWithJSONObject:result options:NSJSONWritingSortedKeys error:NULL];
            fwrite(json.bytes, 1, json.length, stdout); putchar('\n');
            return [mode isEqual:@"roundtrip"] ? 9 : 0;
        }
    }
}
