// Owned research host. Private initializer is invoked only through its runtime
// method signature, never a guessed Swift/C function declaration.
#import <Foundation/Foundation.h>
#import <IOSurface/IOSurface.h>
#import <IOSurface/IOSurfaceObjC.h>
#import <CoreGraphics/CoreGraphics.h>
#import <objc/runtime.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){@autoreleasepool{
 if(argc!=2)return 2;
 NSDictionary *props=@{(id)kIOSurfaceWidth:@3,(id)kIOSurfaceHeight:@2,(id)kIOSurfaceBytesPerElement:@4,(id)kIOSurfaceBytesPerRow:@64,(id)kIOSurfaceAllocSize:@4096,(id)kIOSurfacePixelFormat:@((uint32_t)0x42475241)};
 IOSurfaceRef surface=IOSurfaceCreate((CFDictionaryRef)props);if(!surface)return 3;
 if(IOSurfaceLock(surface,0,NULL)!=kIOReturnSuccess)return 4;
 size_t stride=IOSurfaceGetBytesPerRow(surface),height=IOSurfaceGetHeight(surface),extent=stride*height,alloc=IOSurfaceGetAllocSize(surface);
 if(stride!=64||height!=2||extent!=128||alloc<4096)return 5;
 unsigned char *base=IOSurfaceGetBaseAddress(surface);memset(base,0xa7,alloc);
 const unsigned char pixels[24]={0,0,255,255,0,128,0,128,64,0,0,64,0,0,0,0,12,20,30,80,255,255,255,255};
 for(size_t y=0;y<2;y++){memset(base+y*stride,0xd3+y,stride);memcpy(base+y*stride,pixels+y*12,12);}
 unsigned char expected[128];memcpy(expected,base,128);
 if(IOSurfaceUnlock(surface,0,NULL)!=kIOReturnSuccess)return 6;
 uint32_t sid=IOSurfaceGetID(surface);
 IOSurface *object=[IOSurface alloc];SEL sel=NSSelectorFromString(@"initWithSurfaceID:");
 NSMethodSignature *sig=[object methodSignatureForSelector:sel];
 if(!sig||sig.numberOfArguments!=3||strcmp(sig.methodReturnType,"@")||strcmp([sig getArgumentTypeAtIndex:2],"I")){fprintf(stderr,"signature unavailable or different\n");return 7;}
 NSInvocation *call=[NSInvocation invocationWithMethodSignature:sig];call.target=object;call.selector=sel;[call setArgument:&sid atIndex:2];[call invoke];IOSurface *resolved=nil;[call getReturnValue:&resolved];
 if(!resolved)return 8;
 if(resolved.width!=3||resolved.height!=2||resolved.bytesPerRow!=64||resolved.bytesPerElement!=4)return 9;
 NSData *data=[NSData dataWithBytes:resolved.baseAddress length:resolved.bytesPerRow*resolved.height];
 if(data.length!=128||memcmp(data.bytes,expected,128))return 10;
 CGDataProviderRef provider=CGDataProviderCreateWithCFData((CFDataRef)data);CGColorSpaceRef cs=CGColorSpaceCreateWithName(kCGColorSpaceSRGB);
 CGImageRef image=CGImageCreate(resolved.width,resolved.height,8,resolved.bytesPerElement*8,resolved.bytesPerRow,cs,(CGBitmapInfo)0x2002,provider,NULL,false,kCGRenderingIntentDefault);if(!image)return 11;
 CFDataRef copied=CGDataProviderCopyData(CGImageGetDataProvider(image));if(!copied||CFDataGetLength(copied)!=128||memcmp(CFDataGetBytePtr(copied),expected,128))return 12;
 // Changed source contents after the copy must not alter the copied snapshot.
 if(IOSurfaceLock(surface,0,NULL)!=kIOReturnSuccess)return 13;memset(IOSurfaceGetBaseAddress(surface),0x19,alloc);if(IOSurfaceUnlock(surface,0,NULL)!=kIOReturnSuccess)return 14;
 if(memcmp(data.bytes,expected,128)||memcmp(CFDataGetBytePtr(copied),expected,128))return 15;
 unsigned char output[56];memset(output,0xcd,56);CGContextRef ctx=CGBitmapContextCreate(output,3,2,8,20,cs,kCGBitmapByteOrder32Big|kCGImageAlphaPremultipliedLast);if(!ctx)return 16;
 CGContextSetBlendMode(ctx,kCGBlendModeCopy);CGContextSetInterpolationQuality(ctx,kCGInterpolationNone);CGContextDrawImage(ctx,CGRectMake(0,0,3,2),image);
 NSString *folder=[NSString stringWithUTF8String:argv[1]];
 if(![data writeToFile:[folder stringByAppendingPathComponent:@"snapshot.bin"] atomically:YES])return 17;
 if(![[NSData dataWithBytes:output length:56] writeToFile:[folder stringByAppendingPathComponent:@"output.rgba"] atomically:YES])return 18;
 // Observe lookup with the first receiver retained after creator reference release.
 CFRelease(surface);surface=NULL;
 IOSurface *second=nil;call.target=[IOSurface alloc];[call setArgument:&sid atIndex:2];[call invoke];[call getReturnValue:&second];if(!second||second.surfaceID!=sid||resolved.surfaceID!=sid)return 20;
 NSData *fresh=[NSData dataWithBytes:second.baseAddress length:second.bytesPerRow*second.height];
 unsigned char generation2[128];memset(generation2,0x19,128);if(fresh.length!=128||memcmp(fresh.bytes,generation2,128)||memcmp(data.bytes,expected,128)||memcmp(CFDataGetBytePtr(copied),expected,128))return 21;
 if(![fresh writeToFile:[folder stringByAppendingPathComponent:@"generation2.bin"] atomically:YES])return 22;
 [second release];
 uint32_t missingID=0;IOSurface *missing=nil;call.target=[IOSurface alloc];[call setArgument:&missingID atIndex:2];[call invoke];[call getReturnValue:&missing];if(missing){[missing release];return 19;}
 printf("{\"same_surface_id_new_contents\":true,\"creator_reference_released_before_second_lookup\":true,\"lookup_succeeds_with_retained_receiver_after_creator_release\":true,\"prior_snapshot_unchanged\":true,\"zero_id_returns_nil\":true,\"runtime_initializer_signature_verified\":true,\"initializer_argument\":\"UInt32\",\"width\":3,\"height\":2,\"stride\":%zu,\"allocation\":%zu,\"snapshot_bytes\":128,\"padding_bytes\":104,\"provider_bytes\":128,\"copied_source_mutation_isolated\":true,\"image_bitmap_info\":%u}\n",stride,alloc,(unsigned)CGImageGetBitmapInfo(image));
 CGContextRelease(ctx);CFRelease(copied);CGImageRelease(image);CGColorSpaceRelease(cs);CGDataProviderRelease(provider);[resolved release];if(surface)CFRelease(surface);return 0;
}}
