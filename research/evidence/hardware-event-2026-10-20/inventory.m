#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#include <dlfcn.h>
#include <mach-o/dyld.h>
#include <mach-o/loader.h>
int main(int argc,char **argv){@autoreleasepool{
 if(argc!=2)return 8;
 void *h=dlopen("/System/Library/PrivateFrameworks/PreviewsServicesUI.framework/Versions/A/PreviewsServicesUI",RTLD_NOW|RTLD_LOCAL);if(!h)return 2;
 NSMutableDictionary *out=[NSMutableDictionary dictionary];
 for(NSString *name in @[@"UVHardwareEvent",@"UVFenceHandle"]){Class c=objc_getClass(name.UTF8String);if(!c)return 3;NSMutableArray *rows=[NSMutableArray array];
 for(int meta=0;meta<2;meta++){unsigned n=0;Method *ms=class_copyMethodList(meta?object_getClass(c):c,&n);for(unsigned i=0;i<n;i++){IMP imp=method_getImplementation(ms[i]);Dl_info di={0};dladdr((void*)imp,&di);[rows addObject:@{@"class_method":@(meta!=0),@"selector":NSStringFromSelector(method_getName(ms[i])),@"types":@(method_getTypeEncoding(ms[i])),@"imp":[NSString stringWithFormat:@"0x%llx",(unsigned long long)imp],@"image":di.dli_fname?@(di.dli_fname):@""}];}free(ms);}out[name]=rows;}
 NSMutableArray *images=[NSMutableArray array];for(uint32_t n=0;n<_dyld_image_count();n++){const char *path=_dyld_get_image_name(n);if(!strstr(path,"PreviewsServicesUI.framework"))continue;const struct mach_header_64 *mh=(const struct mach_header_64*)_dyld_get_image_header(n);const uint8_t *lc=(const uint8_t*)(mh+1);for(uint32_t k=0;k<mh->ncmds;k++){const struct load_command *l=(const struct load_command*)lc;if(l->cmd==LC_UUID){const struct uuid_command *u=(const struct uuid_command*)lc;NSMutableString *uuid=[NSMutableString string];for(int j=0;j<16;j++)[uuid appendFormat:@"%02x",u->uuid[j]];[images addObject:@{@"path":@(path),@"uuid":uuid}];}lc+=l->cmdsize;}}
 out[@"images"]=images;for(NSDictionary *row in out[@"UVHardwareEvent"]){unsigned long long a=0;[[NSScanner scannerWithString:row[@"imp"]] scanHexLongLong:&a];NSData *prefix=[NSData dataWithBytes:(void*)a length:32];NSString *file=[NSString stringWithFormat:@"%@/%@.bin",@(argv[1]),[row[@"selector"] stringByReplacingOccurrencesOfString:@":" withString:@"_"]];if(![prefix writeToFile:file atomically:YES])return 9;}
 NSData *d=[NSJSONSerialization dataWithJSONObject:out options:NSJSONWritingPrettyPrinted error:NULL];fwrite(d.bytes,1,d.length,stdout);puts("");return 0;
}}
