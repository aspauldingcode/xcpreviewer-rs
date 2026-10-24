#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#include <dlfcn.h>
int main(void) { @autoreleasepool {
    const char *path="/System/Library/PrivateFrameworks/PreviewsServices.framework/Versions/A/PreviewsServices";
    void *image=dlopen(path,RTLD_NOW|RTLD_LOCAL);
    if(!image){fprintf(stderr,"dlopen failed: %s\n",dlerror());return 2;}
    Class cls=NSClassFromString(@"UVPropertyList");
    if(!cls){fprintf(stderr,"UVPropertyList absent\n");return 3;}
    printf("image\t%s\n",class_getImageName(cls));
    for(unsigned pass=0;pass<2;pass++) {
        unsigned count=0;Method *methods=class_copyMethodList(pass?object_getClass(cls):cls,&count);
        for(unsigned i=0;i<count;i++)printf("%c\t%s\t%s\n",pass?'+':'-',sel_getName(method_getName(methods[i])),method_getTypeEncoding(methods[i]));
        free(methods);
    }
    return 0;
}}
