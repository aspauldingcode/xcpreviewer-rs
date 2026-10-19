// Owned offscreen public JSContext arithmetic probe. No AppKit or Xcode UI.
#import <Foundation/Foundation.h>
#import <JavaScriptCore/JavaScriptCore.h>
#include <unistd.h>
#include <sys/utsname.h>
#include <stdio.h>
#include <stdlib.h>
static void need(BOOL ok, const char *s) { if(!ok){fprintf(stderr,"rejected:%s\n",s);exit(2);} }
static int nibble(unichar c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;return -1;}
int main(int argc,const char **argv){@autoreleasepool{
 alarm(10);fprintf(stderr,"owned_tree_pid:%d\n",getpid());fflush(stderr);
 if(argc==3 && strcmp(argv[1],"--output-control")==0 && strcmp(argv[2],"output-valid")==0){printf("{\"pid\":%d,\"status\":\"owned_output_control\"}\n",getpid());return 0;}
 need(argc==3 && strcmp(argv[1],"--fixture")==0,"args");
 NSString *output=[NSString stringWithUTF8String:argv[2]];
 NSString *root=[output stringByDeletingLastPathComponent];
 NSError *err=nil;NSString *script=[NSString stringWithContentsOfFile:[root stringByAppendingPathComponent:@"probe.js"] encoding:NSUTF8StringEncoding error:&err];need(script!=nil,"script");
 JSContext *context=[[JSContext alloc] init];need(context!=nil,"context");
 __block BOOL exception=NO;context.exceptionHandler=^(JSContext *c,JSValue *v){exception=YES;fprintf(stderr,"owned_js_exception:%s\n",[[v toString] UTF8String]);};
 JSValue *value=[context evaluateScript:script];need(!exception && value!=nil && !value.isUndefined,"evaluation");
 NSData *json=[[value toString] dataUsingEncoding:NSUTF8StringEncoding];need(json!=nil && json.length<262144,"json bound");
 NSMutableDictionary *result=[NSJSONSerialization JSONObjectWithData:json options:NSJSONReadingMutableContainers error:&err];need([result isKindOfClass:[NSMutableDictionary class]],"object");
 NSArray *rows=result[@"rows"];need([rows isKindOfClass:[NSArray class]] && rows.count<=4,"rows");
 NSArray *expected=@[@"wasm-multiply",@"wasm-divide",@"js-multiply",@"js-divide"];
 NSUInteger i=0;
 for(NSMutableDictionary *row in rows){need([row[@"method"] isEqual:expected[i]],"method");NSString *file=[expected[i] stringByAppendingString:@".raw"];need([row[@"file"] isEqual:file],"file");
  NSString *hex=row[@"hex"];need([hex isKindOfClass:[NSString class]] && hex.length==32768,"hex length");NSMutableData *data=[NSMutableData dataWithLength:16384];unsigned char *bytes=data.mutableBytes;
  for(NSUInteger j=0;j<16384;j++){int a=nibble([hex characterAtIndex:j*2]),b=nibble([hex characterAtIndex:j*2+1]);need(a>=0 && b>=0,"hex character");bytes[j]=(a<<4)|b;}
  NSString *path=[output stringByAppendingPathComponent:file];need(![[NSFileManager defaultManager] fileExistsAtPath:path],"no overwrite");need([data writeToFile:path options:NSDataWritingWithoutOverwriting error:&err],"write");[row removeObjectForKey:@"hex"];i++;
 }
 NSBundle *framework=[NSBundle bundleForClass:[JSContext class]];struct utsname u;need(uname(&u)==0,"uname");
 result[@"pid"]=@(getpid());result[@"engine"]=@"public JavaScriptCore JSContext";
 result[@"environment"]=@{@"framework_path":framework.bundlePath?:@"",@"framework_identifier":framework.bundleIdentifier?:@"",@"framework_version":[framework objectForInfoDictionaryKey:@"CFBundleVersion"]?:@"",@"system":[NSString stringWithUTF8String:u.sysname],@"release":[NSString stringWithUTF8String:u.release],@"machine":[NSString stringWithUTF8String:u.machine],@"os_version":[NSProcessInfo processInfo].operatingSystemVersionString};
 result[@"native_UI_execution"]=@NO;result[@"product_integration"]=@NO;result[@"non_Apple_OS_verified"]=@NO;result[@"canvas_qualified"]=@NO;
 NSData *out=[NSJSONSerialization dataWithJSONObject:result options:NSJSONWritingSortedKeys error:&err];need(out!=nil && out.length<8192,"output bound");fwrite(out.bytes,1,out.length,stdout);printf("\n");return 0;
}}
