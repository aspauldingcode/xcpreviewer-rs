// Own-process symbol address resolution only. No entrypoints invoked.
#include <stdio.h>
#include <string.h>
#include <dlfcn.h>
int main(void){if(!dlopen("/System/Library/PrivateFrameworks/PreviewShellKit.framework/Versions/A/PreviewShellKit",RTLD_NOW|RTLD_LOCAL))return 2;char name[4096];unsigned n=0;while(fgets(name,sizeof name,stdin)){if(++n>8192)return 3;size_t k=strlen(name);if(!k||name[k-1]!='\n')return 4;name[k-1]=0;void *p=dlsym(RTLD_DEFAULT,name);if(p)printf("0x%llx %s\n",(unsigned long long)p,name);}return 0;}
