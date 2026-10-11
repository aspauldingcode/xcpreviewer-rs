// Probe serialization of synthetic data only; no service connections are made.
#import <Foundation/Foundation.h>
#import <dlfcn.h>
@interface NSObject (PreviewPropertyList)
- (id)initWithDictionary:(NSDictionary *)dictionary;
- (id)initWithData:(NSData *)data;
- (NSDictionary *)dictionary;
- (NSData *)data;
@end
int main(int argc, const char *argv[]) {
    @autoreleasepool {
        const char *path = argc > 1 ? argv[1] : "/System/Library/PrivateFrameworks/PreviewsServices.framework/PreviewsServices";
        if (!dlopen(path, RTLD_NOW | RTLD_LOCAL)) { fprintf(stderr, "%s\n", dlerror()); return 1; }
        Class cls = NSClassFromString(@"UVPropertyList");
        if (!cls) { fprintf(stderr, "UVPropertyList not registered\n"); return 1; }
        NSDictionary *input = @{@"type": @"synthetic-probe", @"count": @7, @"enabled": @YES,
            @"nested": @{@"name": @"preview"}, @"values": @[@1, @2], @"bytes": [@"hello" dataUsingEncoding:NSUTF8StringEncoding]};
        if (argc > 2) {
            NSData *fixture = [NSData dataWithContentsOfFile:@(argv[2])];
            NSError *fixtureError = nil;
            id value = [NSPropertyListSerialization propertyListWithData:fixture options:NSPropertyListImmutable format:NULL error:&fixtureError];
            if (![value isKindOfClass:NSDictionary.class]) { fprintf(stderr, "Owned fixture must decode as dictionary\n"); return 4; }
            input = value;
        }
        @try {
            id object = [[cls alloc] initWithDictionary:input];
            NSData *data = [object data];
            NSData *repeat = [object data];
            NSData *fresh = [[[cls alloc] initWithDictionary:input] data];
            NSData *foundation = [NSPropertyListSerialization dataWithPropertyList:input format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL];
            NSDictionary *decoded = [[[cls alloc] initWithData:data] dictionary];
            NSPropertyListFormat format = 0;
            NSError *error = nil;
            id standard = [NSPropertyListSerialization propertyListWithData:data options:NSPropertyListImmutable format:&format error:&error];
            NSDictionary *output = @{@"input_kind": @"synthetic dictionary; not a captured preview message",
                @"bytes": @(data.length), @"base64": [data base64EncodedStringWithOptions:0],
                @"repeat_base64": [repeat base64EncodedStringWithOptions:0],
                @"fresh_base64": [fresh base64EncodedStringWithOptions:0],
                @"foundation_base64": [foundation base64EncodedStringWithOptions:0],
                @"uv_round_trip_equal": @([input isEqual:decoded]), @"foundation_decodable": @(standard != nil),
                @"foundation_round_trip_equal": @([input isEqual:standard]), @"foundation_format": @(format),
                @"error": error ? error.description : @""};
            NSData *json = [NSJSONSerialization dataWithJSONObject:output options:NSJSONWritingPrettyPrinted | NSJSONWritingSortedKeys error:&error];
            if (!json) return 2;
            fwrite(json.bytes, 1, json.length, stdout); putchar('\n');
            return [input isEqual:decoded] && [input isEqual:standard] ? 0 : 3;
        } @catch (NSException *exception) { fprintf(stderr, "%s\n", exception.description.UTF8String); return 2; }
    }
}
