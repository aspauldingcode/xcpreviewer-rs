#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#include <dlfcn.h>
int main(void){@autoreleasepool{
 if(!dlopen("/System/Library/PrivateFrameworks/PreviewsServices.framework/Versions/A/PreviewsServices",RTLD_NOW|RTLD_LOCAL))return 2;
 NSArray *names=@[@"_TtC16PreviewsServices11XPCListener",@"_TtC16PreviewsServices13XPCConnection",@"_TtC16PreviewsServices25PreviewsServiceConnection",@"_TtCC16PreviewsServices25PreviewsServiceConnection8Listener"];
 NSMutableArray *rows=[NSMutableArray array];
 for(NSString *name in names){Class cls=NSClassFromString(name);NSMutableDictionary *row=[NSMutableDictionary dictionaryWithDictionary:@{@"class":name,@"present":@(cls!=nil)}];
  if(cls){row[@"image"]=[NSString stringWithUTF8String:class_getImageName(cls)];NSMutableArray *methods=[NSMutableArray array];
   for(unsigned pass=0;pass<2;pass++){unsigned n=0;Method *list=class_copyMethodList(pass?object_getClass(cls):cls,&n);for(unsigned i=0;i<n;i++)[methods addObject:@{@"kind":pass?@"+":@"-",@"selector":[NSString stringWithUTF8String:sel_getName(method_getName(list[i]))],@"encoding":[NSString stringWithUTF8String:method_getTypeEncoding(list[i])]}];free(list);}row[@"methods"]=methods;unsigned count=0;Ivar *ivars=class_copyIvarList(cls,&count);NSMutableArray *fields=[NSMutableArray array];for(unsigned j=0;j<count;j++){const char *type=ivar_getTypeEncoding(ivars[j]);[fields addObject:@{@"name":[NSString stringWithUTF8String:ivar_getName(ivars[j])],@"offset":@(ivar_getOffset(ivars[j])),@"type":type?[NSString stringWithUTF8String:type]:@""}];}free(ivars);row[@"ivars"]=fields;row[@"instance_size"]=@(class_getInstanceSize(cls));
  }[rows addObject:row];
 }
 NSData *data=[NSJSONSerialization dataWithJSONObject:rows options:NSJSONWritingPrettyPrinted|NSJSONWritingSortedKeys error:NULL];fwrite(data.bytes,1,data.length,stdout);putchar('\n');return 0;
}}
