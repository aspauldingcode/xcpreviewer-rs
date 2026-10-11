// Owned public Metal/IOSurface completion control; no private framework calls.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#import <IOSurface/IOSurface.h>
#include <unistd.h>

static NSData *snapshot(IOSurfaceRef surface) {
    if (IOSurfaceLock(surface,kIOSurfaceLockReadOnly,NULL)!=KERN_SUCCESS) return nil;
    NSData *bytes=[NSData dataWithBytes:IOSurfaceGetBaseAddress(surface) length:IOSurfaceGetAllocSize(surface)];
    if (IOSurfaceUnlock(surface,kIOSurfaceLockReadOnly,NULL)!=KERN_SUCCESS) return nil;
    return bytes;
}

int main(int argc,const char **argv) {
    alarm(12);
    @autoreleasepool {
        if (argc!=3) return 2;
        size_t dims[2];
        for(int i=0;i<2;i++) {
            if (!argv[i+1][0] || strlen(argv[i+1])>2 || strspn(argv[i+1],"0123456789")!=strlen(argv[i+1])) return 2;
            dims[i]=strtoul(argv[i+1],NULL,10);
        }
        size_t w=dims[0],h=dims[1];if(!w || w>64 || !h || h>16)return 2;
        id<MTLDevice> device=MTLCreateSystemDefaultDevice();
        if(!device || !device.hasUnifiedMemory)return 3;
        IOSurfaceRef surface=IOSurfaceCreate((__bridge CFDictionaryRef)@{
            (__bridge NSString *)kIOSurfaceWidth:@(w),(__bridge NSString *)kIOSurfaceHeight:@(h),
            (__bridge NSString *)kIOSurfaceBytesPerElement:@4,(__bridge NSString *)kIOSurfacePixelFormat:@((uint32_t)0x42475241)});
        if(!surface)return 4;
        size_t stride=IOSurfaceGetBytesPerRow(surface),allocation=IOSurfaceGetAllocSize(surface);
        if(stride<w*4 || stride>65536 || allocation<stride*h || allocation>1024*1024){CFRelease(surface);return 5;}
        if(IOSurfaceLock(surface,0,NULL)!=KERN_SUCCESS){CFRelease(surface);return 6;}
        memset(IOSurfaceGetBaseAddress(surface),0xa5,allocation);
        if(IOSurfaceUnlock(surface,0,NULL)!=KERN_SUCCESS){CFRelease(surface);return 6;}
        NSData *before=snapshot(surface);if(!before){CFRelease(surface);return 6;}
        MTLTextureDescriptor *descriptor=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatBGRA8Unorm width:w height:h mipmapped:NO];
        descriptor.storageMode=MTLStorageModeShared;descriptor.usage=MTLTextureUsageRenderTarget;
        id<MTLTexture> texture=[device newTextureWithDescriptor:descriptor iosurface:surface plane:0];
        id<MTLCommandQueue> queue=[device newCommandQueue];
        if(!texture || !queue){CFRelease(surface);return 7;}
        BOOL sameSurface=texture.iosurface==surface;
        NSMutableArray *frames=[NSMutableArray array];
        for(unsigned stage=0;stage<3;stage++) { @autoreleasepool {
            id<MTLCommandBuffer> command=[queue commandBuffer];
            MTLRenderPassDescriptor *pass=[MTLRenderPassDescriptor renderPassDescriptor];
            pass.colorAttachments[0].texture=texture;pass.colorAttachments[0].loadAction=MTLLoadActionClear;
            pass.colorAttachments[0].storeAction=MTLStoreActionStore;
            pass.colorAttachments[0].clearColor=stage==2?MTLClearColorMake(0,0,1,1):MTLClearColorMake(1,0,0,1);
            id<MTLRenderCommandEncoder> encoder=[command renderCommandEncoderWithDescriptor:pass];
            if(!command || !encoder){CFRelease(surface);return 8;}[encoder endEncoding];
            dispatch_semaphore_t completed=dispatch_semaphore_create(0);
            __block unsigned calls=0;__block NSUInteger callbackStatus=0;
            [command addCompletedHandler:^(id<MTLCommandBuffer> buffer){calls++;callbackStatus=buffer.status;dispatch_semaphore_signal(completed);}];
            [command commit];
            long waited=dispatch_semaphore_wait(completed,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC));
            if(waited || calls!=1 || callbackStatus!=MTLCommandBufferStatusCompleted || command.status!=MTLCommandBufferStatusCompleted || command.error){CFRelease(surface);return 9;}
            NSData *bytes=snapshot(surface);if(!bytes){CFRelease(surface);return 6;}
            [frames addObject:@{@"stage":@(stage),@"callback_count":@(calls),@"callback_status":@(callbackStatus),@"status":@(command.status),@"error_absent":[NSNumber numberWithBool:command.error==nil],@"bytes_base64":[bytes base64EncodedStringWithOptions:0]}];
        }}
        NSUInteger storageMode=texture.storageMode;
        texture=nil;queue=nil;
        NSData *retained=snapshot(surface);if(!retained){CFRelease(surface);return 6;}
        NSDictionary *result=@{@"width":@(w),@"height":@(h),@"stride":@(stride),@"allocation_bytes":@(allocation),
            @"pixel_format":@(IOSurfaceGetPixelFormat(surface)),@"plane_count":@(IOSurfaceGetPlaneCount(surface)),
            @"bytes_per_element":@(IOSurfaceGetBytesPerElement(surface)),@"texture_storage_mode":@(storageMode),
            @"same_surface":@(sameSurface),@"unified_memory":@(device.hasUnifiedMemory),@"device":device.name,
            @"before_base64":[before base64EncodedStringWithOptions:0],@"after_metal_drop_base64":[retained base64EncodedStringWithOptions:0],@"frames":frames};
        CFRelease(surface);
        NSData *json=[NSJSONSerialization dataWithJSONObject:result options:NSJSONWritingSortedKeys error:NULL];if(!json)return 10;
        fwrite(json.bytes,1,json.length,stdout);putchar('\n');return 0;
    }
}
