#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#include <dlfcn.h>
static NSDictionary *describe(Class cls,const char *selector,BOOL meta){
 Method m=meta?class_getClassMethod(cls,sel_registerName(selector)):class_getInstanceMethod(cls,sel_registerName(selector));if(!m)return @{@"present":@NO};Dl_info image={0};dladdr((const void *)method_getImplementation(m),&image);return @{@"present":@YES,@"encoding":@(method_getTypeEncoding(m)),@"implementation_image":image.dli_fname?@(image.dli_fname):@""};}
int main(int argc,const char **argv){@autoreleasepool{if(argc!=2)return 1;
 NSMutableDictionary *out=[NSMutableDictionary dictionary];out[@"before"]=describe([NSError class],"uv_errorWithUserInfo:",YES);
 void *handle=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);out[@"loaded"]=@(handle!=NULL);if(!handle){const char *error=dlerror();out[@"load_error"]=error?@(error):@"";}
 out[@"after"]=describe([NSError class],"uv_errorWithUserInfo:",YES);
 NSMutableArray *classes=[NSMutableArray array];int count=objc_getClassList(NULL,0);Class *all=(__unsafe_unretained Class *)calloc((size_t)count,sizeof(Class));int actual=objc_getClassList(all,count);for(int i=0;i<MIN(count,actual);i++){const char *name=class_getName(all[i]);if(strstr(name,"HumanReadable")||!strcmp(name,"UVError")||!strcmp(name,"NSError")){NSMutableArray *methods=[NSMutableArray array];for(int mode=0;mode<2;mode++){unsigned n=0;Method *list=class_copyMethodList(mode?object_getClass(all[i]):all[i],&n);for(unsigned j=0;j<n;j++){const char *selector=sel_getName(method_getName(list[j]));if(strstr(selector,"uv_")||strstr(selector,"human")||strstr(selector,"Human")||strstr(selector,"diagnostic")||strstr(selector,"Diagnostic")){[methods addObject:@{@"selector":@(selector),@"class_method":@(mode),@"encoding":@(method_getTypeEncoding(list[j]))}];}}free(list);}[classes addObject:@{@"name":@(name),@"methods":methods}];}}free(all);out[@"classes"]=classes;
 NSData *data=[NSJSONSerialization dataWithJSONObject:out options:NSJSONWritingPrettyPrinted|NSJSONWritingSortedKeys error:NULL];fwrite(data.bytes,1,data.length,stdout);puts("");return 0;}}
