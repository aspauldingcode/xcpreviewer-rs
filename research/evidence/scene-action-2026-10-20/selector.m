#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#include <dlfcn.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
int main(void){@autoreleasepool{if(!dlopen("/System/Library/PrivateFrameworks/PreviewsServicesUI.framework/Versions/A/PreviewsServicesUI",RTLD_NOW|RTLD_LOCAL))return 2;uint64_t p=0;mach_vm_size_t n=0;if(mach_vm_read_overwrite(mach_task_self(),0x29e30fdd8,8,(mach_vm_address_t)&p,&n)||n!=8)return 3;printf("%s\n",sel_getName((SEL)(p&0x0000ffffffffffffULL)));return 0;}}
