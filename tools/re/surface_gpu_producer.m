// Public completion-gated producer linked into the owned Mach peer control.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#import <IOSurface/IOSurface.h>
#include <unistd.h>

static NSData *copy_allocation(IOSurfaceRef s) {
    if(IOSurfaceLock(s,kIOSurfaceLockReadOnly,NULL)!=KERN_SUCCESS)return nil;
    NSData *d=[NSData dataWithBytes:IOSurfaceGetBaseAddress(s) length:IOSurfaceGetAllocSize(s)];
    if(IOSurfaceUnlock(s,kIOSurfaceLockReadOnly,NULL)!=KERN_SUCCESS)return nil;return d;
}

int re_gpu_fill(IOSurfaceRef surface,unsigned seed,const char *folder) {
    @autoreleasepool {
        if(!folder)return 0;
        id<MTLDevice> device=MTLCreateSystemDefaultDevice();if(!device || !device.hasUnifiedMemory)return 0;
        NSData *before=copy_allocation(surface);if(!before)return 0;
        MTLTextureDescriptor *d=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatBGRA8Unorm width:IOSurfaceGetWidth(surface) height:IOSurfaceGetHeight(surface) mipmapped:NO];
        d.storageMode=MTLStorageModeShared;d.usage=MTLTextureUsageRenderTarget;
        id<MTLTexture> texture=[device newTextureWithDescriptor:d iosurface:surface plane:0];
        id<MTLCommandQueue> queue=[device newCommandQueue];if(!texture || !queue || texture.iosurface!=surface)return 0;
        id<MTLCommandBuffer> command=[queue commandBuffer];
        MTLRenderPassDescriptor *pass=[MTLRenderPassDescriptor renderPassDescriptor];
        pass.colorAttachments[0].texture=texture;pass.colorAttachments[0].loadAction=MTLLoadActionClear;
        pass.colorAttachments[0].storeAction=MTLStoreActionStore;
        pass.colorAttachments[0].clearColor=seed>=128?MTLClearColorMake(0,0,1,1):MTLClearColorMake(1,0,0,1);
        id<MTLRenderCommandEncoder> encoder=[command renderCommandEncoderWithDescriptor:pass];if(!command || !encoder)return 0;[encoder endEncoding];
        dispatch_semaphore_t gate=dispatch_semaphore_create(0);__block unsigned calls=0;__block NSUInteger status=0;
        [command addCompletedHandler:^(id<MTLCommandBuffer> b){calls++;status=b.status;dispatch_semaphore_signal(gate);}];
        [command commit];
        if(dispatch_semaphore_wait(gate,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC)) || calls!=1 || status!=MTLCommandBufferStatusCompleted || command.status!=MTLCommandBufferStatusCompleted || command.error)return 0;
        NSData *after=copy_allocation(surface);if(!after)return 0;
        NSDictionary *result=@{@"producer_pid":@(getpid()),@"surface_id":@(IOSurfaceGetID(surface)),@"width":@(IOSurfaceGetWidth(surface)),@"height":@(IOSurfaceGetHeight(surface)),
            @"stride":@(IOSurfaceGetBytesPerRow(surface)),@"allocation_bytes":@(IOSurfaceGetAllocSize(surface)),@"callback_count":@(calls),@"callback_status":@(status),@"status":@(command.status),
            @"error_absent":[NSNumber numberWithBool:command.error==nil],@"unified_memory":@(device.hasUnifiedMemory),@"device":device.name,@"storage_mode":@(texture.storageMode),
            @"before_base64":[before base64EncodedStringWithOptions:0],@"after_base64":[after base64EncodedStringWithOptions:0]};
        NSData *json=[NSJSONSerialization dataWithJSONObject:result options:NSJSONWritingSortedKeys error:NULL];
        NSString *path=[[NSString stringWithUTF8String:folder] stringByAppendingPathComponent:@"gpu-producer.json"];
        return json && [json writeToFile:path atomically:YES];
    }
}
