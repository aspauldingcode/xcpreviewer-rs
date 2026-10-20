// Profile-specific slots derived from UUIDb66e691cf2d13a7294ed78d92a28c252 with current slide.
// Re-derive slots from a fresh mapped image after ASLR/build changes.
// Own-process import-slot observation. No resolved target is invoked.
#import <Foundation/Foundation.h>
#include <dlfcn.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
int main(void){@autoreleasepool{if(!dlopen("/System/Library/PrivateFrameworks/PreviewShellKit.framework/Versions/A/PreviewShellKit",RTLD_NOW|RTLD_LOCAL))return 2;uint64_t slots[]={0x2a79c7220,0x2a79c78e8,0x2a79c78f0,0x2a79c7978,0x2a79c79c8};NSMutableArray *out=[NSMutableArray array];for(unsigned i=0;i<5;i++){uint64_t p=0;mach_vm_size_t n=0;if(mach_vm_read_overwrite(mach_task_self(),slots[i],8,(mach_vm_address_t)&p,&n)!=KERN_SUCCESS||n!=8)return 3;uint64_t a=p&0x0000ffffffffffffULL;Dl_info d={0};if(!dladdr((void*)a,&d))return 4;[out addObject:@{@"slot":[NSString stringWithFormat:@"0x%llx",slots[i]],@"target":[NSString stringWithFormat:@"0x%llx",a],@"symbol":d.dli_sname?@(d.dli_sname):@"",@"image":d.dli_fname?@(d.dli_fname):@""}];}NSData *j=[NSJSONSerialization dataWithJSONObject:out options:NSJSONWritingPrettyPrinted error:NULL];fwrite(j.bytes,1,j.length,stdout);puts("");return 0;}}
