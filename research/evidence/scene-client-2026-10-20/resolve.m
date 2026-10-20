#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#include <dlfcn.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
int main(void){@autoreleasepool{if(!dlopen("/System/Library/PrivateFrameworks/PreviewShellKit.framework/Versions/A/PreviewShellKit",RTLD_NOW|RTLD_LOCAL))return 2;uint64_t slots[]={0x29d995e18,0x29d997018,0x29d996bc0,0x29d9975a8,0x29d995ca8,0x29d9978e0,0x29d995b68,0x29d995870,0x29d9962f8,0x29cdebf60};NSMutableArray *rows=[NSMutableArray array];for(unsigned i=0;i<sizeof slots/sizeof slots[0];i++){uint64_t ptr=0;mach_vm_size_t n=0;if(mach_vm_read_overwrite(mach_task_self(),slots[i],8,(mach_vm_address_t)&ptr,&n)||n!=8)return 3;ptr&=0xffffffffffffULL;const char *name=i==9?class_getName((Class)ptr):sel_getName((SEL)ptr);[rows addObject:@{@"slot":[NSString stringWithFormat:@"0x%llx",slots[i]],@"name":@(name)}];}NSData *d=[NSJSONSerialization dataWithJSONObject:rows options:NSJSONWritingPrettyPrinted error:NULL];fwrite(d.bytes,1,d.length,stdout);puts("");return 0;}}
