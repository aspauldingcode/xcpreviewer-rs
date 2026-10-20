// Research-only public CoreGraphics oracle for the recovered CGImageCreate path.
#include <CoreGraphics/CoreGraphics.h>
#include <CoreFoundation/CoreFoundation.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc,char **argv) {
 if(argc!=5) return 2;
 unsigned long flags=strtoul(argv[1],NULL,0);
 unsigned char input[40],output[56]; memset(output,0xcd,sizeof(output));
 FILE *f=fopen(argv[2],"rb");if(!f)return 3;
 size_t n=fread(input,1,sizeof(input),f);int extra=fgetc(f);fclose(f);
 if(n!=40 || extra!=EOF)return 4;
 CFDataRef data=CFDataCreate(NULL,input,sizeof(input));
 CGDataProviderRef provider=CGDataProviderCreateWithCFData(data);
 CGColorSpaceRef color=CGColorSpaceCreateWithName(kCGColorSpaceSRGB);
 CGImageRef image=CGImageCreate(3,2,8,32,16,color,(CGBitmapInfo)flags,provider,NULL,false,kCGRenderingIntentDefault);
 if(!image)return 5;
 CFDataRef copied=CGDataProviderCopyData(CGImageGetDataProvider(image));
 if(!copied || CFDataGetLength(copied)!=40 || memcmp(input,CFDataGetBytePtr(copied),40))return 6;
 CGContextRef context=CGBitmapContextCreate(output,3,2,8,20,color,kCGBitmapByteOrder32Big|kCGImageAlphaPremultipliedLast);
 if(!context)return 7;
 CGContextSetBlendMode(context,kCGBlendModeCopy);
 CGContextSetInterpolationQuality(context,kCGInterpolationNone);
 CGContextDrawImage(context,CGRectMake(0,0,3,2),image);
 f=fopen(argv[3],"wb");if(!f)return 8;
 size_t written=fwrite(output,1,sizeof(output),f);fclose(f);if(written!=sizeof(output))return 9;
 f=fopen(argv[4],"wb");if(!f)return 10;
 fprintf(f,"{\"bitmap_info\":%u,\"width\":%zu,\"height\":%zu,\"stride\":%zu,\"provider_all_bytes_equal\":true,\"provider_bytes\":40,\"output_bytes\":56}\n",(unsigned)CGImageGetBitmapInfo(image),CGImageGetWidth(image),CGImageGetHeight(image),CGImageGetBytesPerRow(image));fclose(f);
 CGContextRelease(context);CFRelease(copied);CGImageRelease(image);CGColorSpaceRelease(color);CGDataProviderRelease(provider);CFRelease(data);return 0;
}
