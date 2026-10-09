#import <Foundation/Foundation.h>
#import <dlfcn.h>
#import <unistd.h>
@interface NSObject (Probe)
- (id)initWithDictionary:(NSDictionary *)dictionary;
- (NSData *)data;
@end
__attribute__((noinline, visibility("default"))) int preview_probe_tick(int value) { return value + 1; }
int main(int argc, const char *argv[]) {
    @autoreleasepool {
        BOOL preloaded=argc>2 && strcmp(argv[2],"preload")==0;
        if(preloaded && !dlopen("/System/Library/PrivateFrameworks/PreviewsServices.framework/PreviewsServices",RTLD_NOW|RTLD_LOCAL)) return 2;
        if (argc > 1) {
            int waited=0;
            while (access(argv[1], F_OK) != 0 && waited++ < 600) usleep(100000);
            if (access(argv[1], F_OK) != 0) return 4;
        }
        if (!preloaded && !dlopen("/System/Library/PrivateFrameworks/PreviewsServices.framework/PreviewsServices", RTLD_NOW|RTLD_LOCAL)) return 2;
        Class cls=NSClassFromString(@"UVPropertyList");
        if (!cls) return 3;
        for (int i=0; i<6; ++i) {
            @autoreleasepool {
                int value=preview_probe_tick(i);
                id plist=[[cls alloc] initWithDictionary:@{@"type":@"owned-trace-probe",@"value":@(value)}];
                NSData *data=[plist data];
                printf("tick=%d bytes=%lu\n",value,(unsigned long)data.length); fflush(stdout);
            }
            usleep(100000);
        }
    }
    return 0;
}
