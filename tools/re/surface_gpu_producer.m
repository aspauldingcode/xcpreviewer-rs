// Public completion-gated producer linked into the owned Mach peer control.
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#import <IOSurface/IOSurface.h>
#include <unistd.h>
#include <stdatomic.h>

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


int re_gpu_readback(IOSurfaceRef surface,const char *folder) {
    @autoreleasepool {
        size_t w=IOSurfaceGetWidth(surface),h=IOSurfaceGetHeight(surface);
        size_t row=(w*4+255)&~(size_t)255,allocation=16384;
        if(!folder || row*h>allocation)return 0;
        id<MTLDevice> device=MTLCreateSystemDefaultDevice();if(!device || !device.hasUnifiedMemory)return 0;
        MTLTextureDescriptor *d=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatBGRA8Unorm width:w height:h mipmapped:NO];
        d.storageMode=MTLStorageModeShared;d.usage=MTLTextureUsageShaderRead;
        id<MTLTexture> source=[device newTextureWithDescriptor:d iosurface:surface plane:0];
        id<MTLBuffer> destination=[device newBufferWithLength:allocation options:MTLResourceStorageModeShared];
        id<MTLCommandQueue> queue=[device newCommandQueue];if(!source || !destination || !queue || source.iosurface!=surface)return 0;
        memset(destination.contents,0x5c,allocation);
        NSData *before=[NSData dataWithBytes:destination.contents length:allocation];
        id<MTLCommandBuffer> command=[queue commandBuffer];if(!command)return 0;
#ifdef RE_GPU_STALL
        id<MTLSharedEvent> pausedEvent=[device newSharedEvent];if(!pausedEvent || pausedEvent.signaledValue!=0)return 0;
        [command encodeWaitForEvent:pausedEvent value:1];
#endif
        id<MTLBlitCommandEncoder> blit=[command blitCommandEncoder];if(!blit)return 0;
        [blit copyFromTexture:source sourceSlice:0 sourceLevel:0 sourceOrigin:MTLOriginMake(0,0,0) sourceSize:MTLSizeMake(w,h,1) toBuffer:destination destinationOffset:0 destinationBytesPerRow:row destinationBytesPerImage:row*h];
        [blit endEncoding];
        dispatch_semaphore_t gate=dispatch_semaphore_create(0);__block atomic_uint calls=0;__block atomic_ulong status=0;
        [command addCompletedHandler:^(id<MTLCommandBuffer> b){atomic_fetch_add(&calls,1);atomic_store(&status,b.status);dispatch_semaphore_signal(gate);}];[command commit];
#ifdef RE_GPU_STALL
        long firstWait=dispatch_semaphore_wait(gate,dispatch_time(DISPATCH_TIME_NOW,20*NSEC_PER_MSEC));
        unsigned callsBefore=atomic_load(&calls);NSUInteger statusBefore=command.status;uint64_t eventBefore=pausedEvent.signaledValue;
        // Always unblock the owned command before assessing the negative control.
        pausedEvent.signaledValue=1;
        BOOL timeoutControl=firstWait!=0 && callsBefore==0 && eventBefore==0 && (statusBefore==MTLCommandBufferStatusCommitted || statusBefore==MTLCommandBufferStatusScheduled);
#endif
        if(dispatch_semaphore_wait(gate,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC)) || calls!=1 || status!=MTLCommandBufferStatusCompleted || command.status!=MTLCommandBufferStatusCompleted || command.error)return 0;
        #ifdef RE_GPU_STALL
        if(!timeoutControl)return 0;
#endif
        NSData *after=[NSData dataWithBytes:destination.contents length:allocation];
        NSDictionary *result=@{@"consumer_pid":@(getpid()),@"surface_id":@(IOSurfaceGetID(surface)),@"width":@(w),@"height":@(h),@"stride":@(row),@"allocation_bytes":@(allocation),
            @"callback_count":@(atomic_load(&calls)),@"callback_status":@(atomic_load(&status)),@"status":@(command.status),@"error_absent":[NSNumber numberWithBool:command.error==nil],
            @"unified_memory":@(device.hasUnifiedMemory),@"source_storage_mode":@(source.storageMode),@"destination_storage_mode":@(destination.storageMode),@"device":device.name,
            @"before_base64":[before base64EncodedStringWithOptions:0],@"after_base64":[after base64EncodedStringWithOptions:0]};
        NSMutableDictionary *metrics=[result mutableCopy];
#ifdef RE_GPU_STALL
        metrics[@"stall"]=@{@"timeout_observed":[NSNumber numberWithBool:firstWait!=0],@"callbacks_before_release":@(callsBefore),@"status_before_release":@(statusBefore),@"event_before_release":@(eventBefore),@"event_after_release":@(pausedEvent.signaledValue),@"wait_deadline_ns":@20000000,@"initial_wait_completion_accepted":@NO};
#endif
        NSData *json=[NSJSONSerialization dataWithJSONObject:metrics options:NSJSONWritingSortedKeys error:NULL];
        NSString *path=[[NSString stringWithUTF8String:folder] stringByAppendingPathComponent:@"gpu-consumer.json"];
        return json && [json writeToFile:path atomically:YES];
    }
}
