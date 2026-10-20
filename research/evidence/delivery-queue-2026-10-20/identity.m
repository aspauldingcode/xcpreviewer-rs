#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#include <dlfcn.h>
int main(void){@autoreleasepool{if(!dlopen("/System/Library/PrivateFrameworks/PreviewsServicesUI.framework/Versions/A/PreviewsServicesUI",RTLD_NOW|RTLD_LOCAL))return 2;Class c=NSClassFromString(@"BSServiceQueue");IMP p=method_getImplementation(class_getInstanceMethod(c,NSSelectorFromString(@"performAfter:withBlock:")));Dl_info d={0};if(!dladdr((void*)p,&d))return 3;printf("%s\n",d.dli_fname);return 0;}}
