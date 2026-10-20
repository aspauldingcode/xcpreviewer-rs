// Native research oracle only; no event posting or target application access.
#import <Foundation/Foundation.h>
#import <CoreGraphics/CoreGraphics.h>
int main(int argc,char **argv){@autoreleasepool{if(argc!=2)return 2;NSData *d=[NSData dataWithContentsOfFile:@(argv[1])];if(!d||d.length>1048576)return 3;CGEventRef e=CGEventCreateFromData(NULL,(CFDataRef)d);if(!e){puts("{\"accepted\":false}");return 0;}NSDictionary *r=@{@"accepted":@YES,@"type":@(CGEventGetType(e)),@"timestamp":@(CGEventGetTimestamp(e)),@"flags":@(CGEventGetFlags(e))};NSData *j=[NSJSONSerialization dataWithJSONObject:r options:0 error:NULL];fwrite(j.bytes,1,j.length,stdout);puts("");CFRelease(e);return 0;}}
