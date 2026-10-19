// Owned offscreen public Quartz byte normalization; no AppKit/SwiftUI/Canvas.
#include <CoreGraphics/CoreGraphics.h>
#include <CoreFoundation/CoreFoundation.h>
#include <CommonCrypto/CommonDigest.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
static int save(const char *root,const char *name,const void *raw,size_t n){char path[4096];if(snprintf(path,sizeof(path),"%s/%s",root,name)>=(int)sizeof(path))return 0;FILE *f=fopen(path,"wb");if(!f)return 0;size_t wrote=fwrite(raw,1,n,f);int closed=fclose(f);return wrote==n&&closed==0;}
static void hash(const void *raw,size_t n,char out[65]){unsigned char digest[CC_SHA256_DIGEST_LENGTH];CC_SHA256(raw,(CC_LONG)n,digest);for(int i=0;i<32;i++)sprintf(out+i*2,"%02x",digest[i]);}
static int run(int route,const char *folder){
 const size_t width=256,height=3,srcstride=route?4160:1088,srcsize=srcstride*height,dststride=4160,dstsize=16384;
 unsigned char *src=NULL,*dst=NULL;CFDataRef bytes=NULL,copied=NULL;CGDataProviderRef provider=NULL;CGImageRef image=NULL;CGContextRef context=NULL;CGColorSpaceRef space=NULL;int ok=0;
 src=malloc(srcsize);dst=malloc(dstsize);if(!src||!dst)goto done;memset(src,0xa5,srcsize);memset(dst,0xa5,dstsize);
 for(size_t y=0;y<height;y++){memset(dst+y*dststride,0,width*16);for(size_t x=0;x<width;x++)for(size_t c=0;c<4;c++){unsigned code=c==3?255:(unsigned)((x+c*85)&255);if(route){float value=(float)((double)code/255.0);memcpy(src+y*srcstride+x*16+c*4,&value,4);}else src[y*srcstride+x*4+c]=(unsigned char)code;}}
 space=CGColorSpaceCreateWithName(kCGColorSpaceLinearSRGB);if(!space)goto done;bytes=CFDataCreate(kCFAllocatorDefault,src,srcsize);if(!bytes)goto done;provider=CGDataProviderCreateWithCFData(bytes);if(!provider)goto done;
 CGBitmapInfo floatinfo=kCGBitmapFloatComponents|kCGBitmapByteOrder32Little|kCGImageAlphaPremultipliedLast;
 image=CGImageCreate(width,height,route?32:8,route?128:32,srcstride,space,route?floatinfo:kCGImageAlphaPremultipliedLast,provider,NULL,false,kCGRenderingIntentDefault);if(!image)goto done;
 copied=CGDataProviderCopyData(CGImageGetDataProvider(image));if(!copied||CFDataGetLength(copied)!=(CFIndex)srcsize||memcmp(CFDataGetBytePtr(copied),src,srcsize))goto done;
 context=CGBitmapContextCreate(dst,width,height,32,dststride,space,floatinfo);if(!context)goto done;CGContextSetBlendMode(context,kCGBlendModeCopy);CGContextSetInterpolationQuality(context,kCGInterpolationNone);CGContextDrawImage(context,CGRectMake(0,0,width,height),image);
 char input[64],output[64],ih[65],oh[65],color[128]={0};snprintf(input,sizeof(input),"route%d-provider.raw",route);snprintf(output,sizeof(output),"route%d-readback.raw",route);hash(src,srcsize,ih);hash(dst,dstsize,oh);if(!save(folder,input,src,srcsize)||!save(folder,output,dst,dstsize)||!CFStringGetCString(CGColorSpaceGetName(space),color,sizeof(color),kCFStringEncodingUTF8))goto done;
 if(printf("{\"pid\":%d,\"route\":%d,\"provider_file\":\"%s\",\"file\":\"%s\",\"provider_sha256\":\"%s\",\"sha256\":\"%s\",\"provider_bytes\":%zu,\"width\":%zu,\"height\":%zu,\"image_stride\":%zu,\"image_bits_per_component\":%zu,\"image_bits_per_pixel\":%zu,\"image_bitmap_info\":%u,\"stride\":%zu,\"allocation_bytes\":%zu,\"bits_per_component\":%zu,\"bits_per_pixel\":%zu,\"bitmap_info\":%u,\"color_space\":\"%s\"}\n",getpid(),route,input,output,ih,oh,srcsize,width,height,CGImageGetBytesPerRow(image),CGImageGetBitsPerComponent(image),CGImageGetBitsPerPixel(image),CGImageGetBitmapInfo(image),CGBitmapContextGetBytesPerRow(context),dstsize,CGBitmapContextGetBitsPerComponent(context),CGBitmapContextGetBitsPerPixel(context),CGBitmapContextGetBitmapInfo(context),color)<0)goto done;ok=1;
 done:if(context)CGContextRelease(context);if(copied)CFRelease(copied);if(image)CGImageRelease(image);if(provider)CGDataProviderRelease(provider);if(bytes)CFRelease(bytes);if(space)CGColorSpaceRelease(space);free(src);free(dst);return ok?0:76;
}
int main(int argc,char **argv){alarm(10);if(dprintf(2,"owned_tree_pid:%d\n",getpid())<0)return 84;if(argc==3&&!strcmp(argv[1],"--output-control")&&!strcmp(argv[2],"output-valid"))return printf("{\"pid\":%d,\"status\":\"owned_output_control\"}\n",getpid())<0?83:0;if(argc!=3||strcmp(argv[1],"--fixture"))return 2;for(int i=0;i<2;i++){int code=run(i,argv[2]);if(code)return code;}return fflush(stdout)==0&&!ferror(stdout)?0:83;}
