// Research-only public CoreGraphics interposition. Never injected into Xcode.
#include <CoreGraphics/CoreGraphics.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static void event(const char *kind, const void *object) {
 const char *path=getenv("OWNED_CG_TRACE"); if(!path)return;
 int fd=open(path,O_WRONLY|O_CREAT|O_APPEND,0600);if(fd<0)_exit(120);
 char b[160];int n=snprintf(b,sizeof b,"%d %s %p\n",getpid(),kind,object);
 if(n<=0 || n>=(int)sizeof b || write(fd,b,n)!=n){close(fd);_exit(121);}close(fd);
}
__attribute__((constructor)) static void loaded(void){event("loaded",NULL);}
static CGImageRef observed_create(size_t w,size_t h,size_t bpc,size_t bpp,size_t row,CGColorSpaceRef cs,CGBitmapInfo info,CGDataProviderRef provider,const CGFloat *decode,bool interpolate,CGColorRenderingIntent intent){
 event("create-enter",NULL);
 CGImageRef image=CGImageCreate(w,h,bpc,bpp,row,cs,info,provider,decode,interpolate,intent);
 event("create-return",image);return image;
}
static CGImageRef observed_retain(CGImageRef image){event("retain-enter",image);CGImageRef r=CGImageRetain(image);event("retain-return",r);return r;}
static void observed_release(CGImageRef image){event("release-enter",image);CGImageRelease(image);event("release-return",image);}
#define INTERPOSE(replacement,original) __attribute__((used)) static const struct {const void *replacement;const void *original;} pair_##original __attribute__((section("__DATA,__interpose")))={(const void *)(uintptr_t)&replacement,(const void *)(uintptr_t)&original};
INTERPOSE(observed_create,CGImageCreate)
INTERPOSE(observed_retain,CGImageRetain)
INTERPOSE(observed_release,CGImageRelease)
