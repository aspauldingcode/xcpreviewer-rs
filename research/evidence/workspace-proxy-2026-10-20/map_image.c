// Research-only reader of one image mapped into this newly owned process.
// No target code entrypoint is invoked; raw bytes must remain local.
#include <mach-o/dyld.h>
#include <mach-o/loader.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <objc/runtime.h>
int main(int argc,char **argv){
 if(argc!=2)return 2;
 const char *path="/System/Library/PrivateFrameworks/FrontBoardServices.framework/Versions/A/FrontBoardServices";
 void *handle=dlopen(path,RTLD_NOW|RTLD_LOCAL);if(!handle){fprintf(stderr,"%s\n",dlerror());return 3;}
 const struct mach_header_64 *header=NULL;intptr_t slide=0;
 for(uint32_t i=0;i<_dyld_image_count();i++){if(!strcmp(_dyld_get_image_name(i),path)){header=(const struct mach_header_64 *)_dyld_get_image_header(i);slide=_dyld_get_image_vmaddr_slide(i);break;}}
 if(!header||header->magic!=MH_MAGIC_64||header->ncmds>4096||header->sizeofcmds>1024*1024)return 4;
 char out[2048];if(snprintf(out,sizeof out,"%s/mapped.json",argv[1])>=(int)sizeof out)return 5;
 FILE *meta=fopen(out,"wb");if(!meta)return 6;
 fprintf(meta,"{\"path\":\"%s\",\"slide\":\"0x%llx\",\"cpu\":%u,\"subtype\":%u,\"segments\":[",path,(unsigned long long)slide,header->cputype,header->cpusubtype);
 const unsigned char *p=(const unsigned char *)(header+1),*end=p+header->sizeofcmds;size_t total=0;unsigned count=0;char uuid[33]={0};
 for(uint32_t i=0;i<header->ncmds;i++){
  if(p+sizeof(struct load_command)>end)return 7;const struct load_command *lc=(const struct load_command *)p;if(lc->cmdsize<8||p+lc->cmdsize>end)return 8;
  if(lc->cmd==LC_UUID){const struct uuid_command *u=(const struct uuid_command *)p;for(int j=0;j<16;j++)snprintf(uuid+j*2,3,"%02x",u->uuid[j]);}
  if(lc->cmd==LC_SEGMENT_64){const struct segment_command_64 *s=(const struct segment_command_64 *)p;
   if((s->initprot&VM_PROT_READ)&&s->vmsize&&strncmp(s->segname,"__LINKEDIT",16)){
    if(s->vmsize>32*1024*1024||total+s->vmsize>64*1024*1024||count>=32)return 9;total+=s->vmsize;
    void *buf=malloc((size_t)s->vmsize);if(!buf)return 10;mach_vm_size_t n=0;
    if(mach_vm_read_overwrite(mach_task_self(),s->vmaddr+slide,s->vmsize,(mach_vm_address_t)buf,&n)!=KERN_SUCCESS||n!=s->vmsize)return 11;
    snprintf(out,sizeof out,"%s/segment-%02u.bin",argv[1],count);FILE *f=fopen(out,"wb");if(!f||fwrite(buf,1,(size_t)n,f)!=(size_t)n)return 12;fclose(f);free(buf);
    fprintf(meta,"%s{\"name\":\"%.16s\",\"address\":\"0x%llx\",\"unslid\":\"0x%llx\",\"size\":%llu,\"protection\":%u,\"file\":\"segment-%02u.bin\"}",count?",":"",s->segname,(unsigned long long)(s->vmaddr+slide),(unsigned long long)s->vmaddr,(unsigned long long)n,s->initprot,count);count++;
   }
  }p+=lc->cmdsize;
 }
 fprintf(meta,"],\"uuid\":\"%s\",\"symbols\":[",uuid);
 const char *names[]={"WorkspaceInterface","WorkspaceInvertedInterface","WorkspaceReceiveActions"};const char *classes[]={"FBSWorkspaceServiceSpecification","FBSWorkspaceServiceSpecification","FBSWorkspaceScenesClient"};const char *selectors[]={"interface","invertedInterface","sceneID:sendActions:toExtension:completion:"};_Static_assert(sizeof names==sizeof classes && sizeof names==sizeof selectors,"probe arrays must agree");
 for(unsigned i=0;i<sizeof names/sizeof names[0];i++){Class c=objc_getClass(classes[i]);Method method=(i<2?class_getClassMethod(c,sel_registerName(selectors[i])):class_getInstanceMethod(c,sel_registerName(selectors[i])));if(!method)return 17;void *symbol=(void*)method_getImplementation(method);Dl_info identity={0};if(!dladdr(symbol,&identity)||strcmp(identity.dli_fname,path))return 18;unsigned char prefix[32];mach_vm_size_t n=0;if(mach_vm_read_overwrite(mach_task_self(),(mach_vm_address_t)(uintptr_t)symbol,32,(mach_vm_address_t)prefix,&n)!=KERN_SUCCESS||n!=32)return 14;snprintf(out,sizeof out,"%s/symbol-%u.bin",argv[1],i);FILE *f=fopen(out,"wb");if(!f||fwrite(prefix,1,32,f)!=32)return 15;fclose(f);fprintf(meta,"%s{\"name\":\"%s\",\"address\":\"0x%llx\"}",i?",":"",names[i],(unsigned long long)(uintptr_t)symbol);}

 fprintf(meta,"],\"bytes\":%zu}\n",total);fclose(meta);printf("mapped selected image: %u segments, %zu bytes; entrypoints resolved only\n",count,total);return 0;
}
