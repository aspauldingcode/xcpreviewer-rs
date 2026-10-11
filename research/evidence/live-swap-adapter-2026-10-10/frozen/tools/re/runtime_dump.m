// Enumerate metadata in an isolated process. No private methods are invoked.
#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#import <mach-o/dyld.h>
#import <mach-o/loader.h>
#import <dlfcn.h>

static NSString *string(const char *value) { return value ? @(value) : @""; }
static NSArray *methods(Class cls) {
    unsigned count = 0;
    Method *list = class_copyMethodList(cls, &count);
    NSMutableArray *result = [NSMutableArray array];
    for (unsigned i = 0; i < count; ++i) {
        [result addObject:@{@"selector": string(sel_getName(method_getName(list[i]))),
                            @"encoding": string(method_getTypeEncoding(list[i]))}];
    }
    free(list);
    return [result sortedArrayUsingDescriptors:@[[NSSortDescriptor sortDescriptorWithKey:@"selector" ascending:YES]]];
}
static BOOL relevant(const char *value) {
    NSString *s = string(value);
    return [s containsString:@"Previews"] || [s hasPrefix:@"UV"] || [s hasPrefix:@"XCPreview"];
}
int main(int argc, const char *argv[]) {
    @autoreleasepool {
        NSMutableArray *loads = [NSMutableArray array];
        BOOL failed = NO;
        for (int i = 1; i < argc; ++i) {
            void *handle = dlopen(argv[i], RTLD_NOW | RTLD_LOCAL);
            const char *error = handle ? NULL : dlerror();
            [loads addObject:@{@"path": string(argv[i]), @"loaded": @(handle != NULL), @"error": string(error)}];
            failed |= handle == NULL;
        }
        unsigned count = 0;
        Class *classes = objc_copyClassList(&count);
        NSMutableArray *records = [NSMutableArray array];
        for (unsigned i = 0; i < count; ++i) {
            const char *image = class_getImageName(classes[i]);
            if (!relevant(image)) continue;
            NSMutableArray *protocols = [NSMutableArray array];
            unsigned n = 0;
            Protocol *__unsafe_unretained *ps = class_copyProtocolList(classes[i], &n);
            for (unsigned j = 0; j < n; ++j) [protocols addObject:string(protocol_getName(ps[j]))];
            free(ps);
            [records addObject:@{@"name": string(class_getName(classes[i])), @"image": string(image),
                @"superclass": string(class_getName(class_getSuperclass(classes[i]))),
                @"instance_methods": methods(classes[i]), @"class_methods": methods(object_getClass(classes[i])),
                @"protocols": [protocols sortedArrayUsingSelector:@selector(compare:)]}];
        }
        free(classes);
        NSMutableArray *protocolRecords = [NSMutableArray array];
        Protocol *__unsafe_unretained *protocols = objc_copyProtocolList(&count);
        for (unsigned i = 0; i < count; ++i) {
            if (!relevant(protocol_getName(protocols[i]))) continue;
            NSMutableArray *ms = [NSMutableArray array];
            for (int required = 0; required <= 1; ++required) {
                for (int instance = 0; instance <= 1; ++instance) {
                    unsigned n = 0;
                    struct objc_method_description *list = protocol_copyMethodDescriptionList(protocols[i], required, instance, &n);
                    for (unsigned j = 0; j < n; ++j) [ms addObject:@{@"selector": string(sel_getName(list[j].name)),
                        @"encoding": string(list[j].types), @"required": @(required), @"instance": @(instance)}];
                    free(list);
                }
            }
            [protocolRecords addObject:@{@"name": string(protocol_getName(protocols[i])), @"methods": ms}];
        }
        free(protocols);
        NSMutableArray *images = [NSMutableArray array];
        for (uint32_t i = 0; i < _dyld_image_count(); ++i) {
            const char *name = _dyld_get_image_name(i);
            if (!relevant(name)) continue;
            const struct mach_header *header = _dyld_get_image_header(i);
            const uint8_t *cursor = (const uint8_t *)header + (header->magic == MH_MAGIC_64 ? sizeof(struct mach_header_64) : sizeof(struct mach_header));
            NSString *uuid = @"";
            for (uint32_t j = 0; j < header->ncmds; ++j) {
                const struct load_command *cmd = (const struct load_command *)cursor;
                if (cmd->cmd == LC_UUID) uuid = [[[NSUUID alloc] initWithUUIDBytes:((const struct uuid_command *)cursor)->uuid] UUIDString];
                cursor += cmd->cmdsize;
            }
            [images addObject:@{@"path": string(name), @"uuid": uuid}];
        }
        // ObjC enumeration does not expose the fields of pure Swift structs/enums.
        NSDictionary *output = @{@"loads": loads, @"images": images,
            @"classes": [records sortedArrayUsingDescriptors:@[[NSSortDescriptor sortDescriptorWithKey:@"name" ascending:YES]]],
            @"protocols": [protocolRecords sortedArrayUsingDescriptors:@[[NSSortDescriptor sortDescriptorWithKey:@"name" ascending:YES]]]};
        NSError *error = nil;
        NSData *json = [NSJSONSerialization dataWithJSONObject:output options:NSJSONWritingPrettyPrinted | NSJSONWritingSortedKeys error:&error];
        if (!json) { fprintf(stderr, "%s\n", error.description.UTF8String); return 2; }
        fwrite(json.bytes, 1, json.length, stdout);
        putchar('\n');
        return failed ? 1 : 0;
    }
}
