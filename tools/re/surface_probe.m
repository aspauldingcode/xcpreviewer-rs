// Public IOSurface API, owned CPU-written surfaces, local XPC objects only.
#import <Foundation/Foundation.h>
#import <IOSurface/IOSurface.h>
#import <xpc/xpc.h>

static NSData *snapshot(IOSurfaceRef surface) {
    if (IOSurfaceLock(surface,kIOSurfaceLockReadOnly,NULL)!=KERN_SUCCESS) return nil;
    size_t count=IOSurfaceGetBytesPerRow(surface)*IOSurfaceGetHeight(surface);
    NSData *data=[NSData dataWithBytes:IOSurfaceGetBaseAddress(surface) length:count];
    if (IOSurfaceUnlock(surface,kIOSurfaceLockReadOnly,NULL)!=KERN_SUCCESS) return nil;
    return data;
}

int main(int argc,const char *argv[]) {
    @autoreleasepool {
        if (argc!=4) return 2;
        unsigned long values[3];
        for(int i=0;i<3;i++) {
            if (!argv[i+1][0] || strlen(argv[i+1])>3 || strspn(argv[i+1],"0123456789")!=strlen(argv[i+1])) return 2;
            values[i]=strtoul(argv[i+1],NULL,10);
        }
        size_t width=values[0],height=values[1];unsigned seed=values[2];
        if (!width || width>64 || !height || height>16 || seed>255) return 2;
        NSDictionary *properties=@{(__bridge NSString *)kIOSurfaceWidth:@(width),(__bridge NSString *)kIOSurfaceHeight:@(height),
            (__bridge NSString *)kIOSurfaceBytesPerElement:@4,(__bridge NSString *)kIOSurfacePixelFormat:@((uint32_t)0x42475241)};
        IOSurfaceRef original=IOSurfaceCreate((__bridge CFDictionaryRef)properties);if (!original) return 3;
        size_t stride=IOSurfaceGetBytesPerRow(original),allocation=IOSurfaceGetAllocSize(original);
        if (stride<width*4 || stride>65536 || allocation<stride*height || allocation>1024*1024) {CFRelease(original);return 4;}
        if(IOSurfaceLock(original,0,NULL)!=KERN_SUCCESS){CFRelease(original);return 5;}
        uint8_t *base=IOSurfaceGetBaseAddress(original);memset(base,0xa5,allocation);
        for(size_t y=0;y<height;y++) for(size_t x=0;x<width;x++) for(size_t c=0;c<4;c++)
            base[y*stride+x*4+c]=c==3?255:(seed+x*17+y*31+c*53)&255;
        if(IOSurfaceUnlock(original,0,NULL)!=KERN_SUCCESS){CFRelease(original);return 5;}
        IOSurfaceID originalID=IOSurfaceGetID(original);
        xpc_object_t resource=IOSurfaceCreateXPCObject(original);CFRelease(original);
        if(!resource)return 6;
        BOOL isData=xpc_get_type(resource)==XPC_TYPE_DATA;
        IOSurfaceRef first=IOSurfaceLookupFromXPCObject(resource),second=IOSurfaceLookupFromXPCObject(resource);
        if(!first || !second){if(first)CFRelease(first);if(second)CFRelease(second);return 7;}
        BOOL sameID=IOSurfaceGetID(first)==originalID && IOSurfaceGetID(second)==originalID;
        NSData *before=snapshot(second);
        // Lookup references remain owned after the original and XPC holder release.
        resource=nil;
        if(IOSurfaceLock(first,0,NULL)!=KERN_SUCCESS){CFRelease(first);CFRelease(second);return 5;}
        ((uint8_t *)IOSurfaceGetBaseAddress(first))[0]^=0x5a;
        if(IOSurfaceUnlock(first,0,NULL)!=KERN_SUCCESS){CFRelease(first);CFRelease(second);return 5;}
        CFRelease(first);
        NSData *after=snapshot(second);
        NSDictionary *result=@{@"width":@(IOSurfaceGetWidth(second)),@"height":@(IOSurfaceGetHeight(second)),@"seed":@(seed),
            @"stride":@(stride),@"allocation_bytes":@(allocation),@"bytes_per_element":@(IOSurfaceGetBytesPerElement(second)),
            @"pixel_format":@(IOSurfaceGetPixelFormat(second)),@"plane_count":@(IOSurfaceGetPlaneCount(second)),@"same_surface_id":@(sameID),@"xpc_is_data":@(isData),
            @"before_base64":before?[before base64EncodedStringWithOptions:0]:@"",@"after_base64":after?[after base64EncodedStringWithOptions:0]:@"",
            @"scope":@"Owned single-plane BGRA memory via local IOSurface XPC holders. No service connection, GPU synchronization, cross-process transfer or canvas snapshot"};
        CFRelease(second);
        NSData *json=[NSJSONSerialization dataWithJSONObject:result options:NSJSONWritingSortedKeys error:NULL];if(!json)return 8;
        fwrite(json.bytes,1,json.length,stdout);putchar('\n');return 0;
    }
}
