#import <Foundation/Foundation.h>
#include <dlfcn.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
int main(void){@autoreleasepool{if(!dlopen("/System/Library/PrivateFrameworks/PreviewsServicesUI.framework/Versions/A/PreviewsServicesUI",RTLD_NOW|RTLD_LOCAL))return 2;for(uint64_t a=0x29ce5a7b0;a<=0x29ce5a7b8;a+=8){uint64_t p=0;mach_vm_size_t n=0;if(mach_vm_read_overwrite(mach_task_self(),a,8,(mach_vm_address_t)&p,&n)||n!=8)return 3;printf("0x%llx 0x%llx\n",a,p&0x0000ffffffffffffULL);}for(const char **n=(const char*[]){"_swiftEmptyArrayStorage","_swiftEmptyDictionarySingleton",NULL};*n;n++)printf("%s 0x%llx\n",*n,(unsigned long long)dlsym(RTLD_DEFAULT,*n));return 0;}}
