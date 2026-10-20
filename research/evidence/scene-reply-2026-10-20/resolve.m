#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#include <dlfcn.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
int main(void){@autoreleasepool{if(!dlopen("/System/Library/PrivateFrameworks/PreviewsServicesUI.framework/Versions/A/PreviewsServicesUI",RTLD_NOW|RTLD_LOCAL))return 2;NSMutableArray *out=[NSMutableArray array];uint64_t a[]={0x29e30fe58,0x29e30fe60,0x29e30fe68,0x29e30fdd8,0x29e30fd68,0x29cdebf50,0x29cdec020,0x29ce216a0};for(unsigned i=0;i<8;i++){uint64_t p=0;mach_vm_size_t n=0;if(mach_vm_read_overwrite(mach_task_self(),a[i],8,(mach_vm_address_t)&p,&n)||n!=8)return 3;p&=0x0000ffffffffffffULL;const char *name=i<5?sel_getName((SEL)p):class_getName((Class)p);[out addObject:@{@"slot":[NSString stringWithFormat:@"0x%llx",a[i]],@"name":@(name)}];}NSData *d=[NSJSONSerialization dataWithJSONObject:out options:NSJSONWritingPrettyPrinted error:NULL];fwrite(d.bytes,1,d.length,stdout);puts("");return 0;}}
