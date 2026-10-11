// Owned finite data controls only; no service contact or Swift ABI invocation.
#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#import <dlfcn.h>
#import <mach-o/loader.h>
@interface NSObject (OwnedPlistDecode)
- (id)initWithData:(NSData *)data;
- (id)dictionary;
- (NSData *)data;
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


int main(int argc,const char **argv) {
 @autoreleasepool {
  if(argc!=2)return 2;
  NSData *input=[NSData dataWithContentsOfFile:@(argv[1])];if(!input || input.length>65536)return 2;
  if(!dlopen("/System/Library/PrivateFrameworks/PreviewsServices.framework/PreviewsServices",RTLD_NOW|RTLD_LOCAL))return 3;
  Class cls=NSClassFromString(@"UVPropertyList");
  Method init=class_getInstanceMethod(cls,@selector(initWithData:)),dict=class_getInstanceMethod(cls,@selector(dictionary)),data=class_getInstanceMethod(cls,@selector(data));
  if(!init || !dict || !data || strcmp(method_getTypeEncoding(init),"@24@0:8@16") || strcmp(method_getTypeEncoding(dict),"@16@0:8") || strcmp(method_getTypeEncoding(data),"@16@0:8"))return 4;
  NSMutableDictionary *r=[@{@"image":imageIdentity(init),@"input_base64":[input base64EncodedStringWithOptions:0]} mutableCopy];
  NSString *phase=@"init";
  @try {
   id object=[[cls alloc] initWithData:input];r[@"object_present"]=@((BOOL)(object!=nil));
   phase=@"data";NSData *encoded=[object data];r[@"data_present"]=@((BOOL)(encoded!=nil));if(encoded)r[@"data_base64"]=[encoded base64EncodedStringWithOptions:0];
   phase=@"dictionary";id value=[object dictionary];r[@"value_present"]=@((BOOL)(value!=nil));r[@"dictionary_type"]=@([value isKindOfClass:NSDictionary.class]);
   if(value && [NSPropertyListSerialization propertyList:value isValidForFormat:NSPropertyListBinaryFormat_v1_0]) {
    NSData *plist=[NSPropertyListSerialization dataWithPropertyList:value format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL];
    if(plist)r[@"value_base64"]=[plist base64EncodedStringWithOptions:0];
   }
   r[@"outcome"]=@"returned";
  } @catch(NSException *e) {r[@"outcome"]=@"exception";r[@"phase"]=phase;r[@"exception_name"]=e.name;}
  NSError *error=nil;id value=[NSPropertyListSerialization propertyListWithData:input options:NSPropertyListImmutable format:NULL error:&error];
  r[@"foundation_present"]=@((BOOL)(value!=nil));r[@"foundation_dictionary"]=@([value isKindOfClass:NSDictionary.class]);
  if(value) {NSData *plist=[NSPropertyListSerialization dataWithPropertyList:value format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL];if(plist)r[@"foundation_value_base64"]=[plist base64EncodedStringWithOptions:0];}
  r[@"foundation_error_code"]=error ? @(error.code) : @0;
  NSData *json=[NSJSONSerialization dataWithJSONObject:r options:NSJSONWritingSortedKeys error:NULL];if(!json)return 5;
  fwrite(json.bytes,1,json.length,stdout);putchar('\n');return 0;
 }
}
