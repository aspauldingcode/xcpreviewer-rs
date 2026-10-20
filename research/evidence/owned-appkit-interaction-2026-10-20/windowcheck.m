// Fresh WindowServer metadata query for one exact owned child PID.
#import <Foundation/Foundation.h>
#import <CoreGraphics/CoreGraphics.h>
#include <unistd.h>
#include <stdlib.h>
int main(int argc,char **argv){@autoreleasepool{if(argc!=2)return 2;int pid=atoi(argv[1]);if(pid<=0)return 3;for(int attempt=0;attempt<20;attempt++){CFArrayRef a=CGWindowListCopyWindowInfo(kCGWindowListOptionAll,kCGNullWindowID);if(!a)return 4;unsigned count=0;for(NSDictionary *w in (NSArray*)a)if([w[(id)kCGWindowOwnerPID] intValue]==pid)count++;CFRelease(a);if(!count){printf("{\"owned_pid\":%d,\"owned_windows_remaining\":0,\"fresh_queries\":%d}\n",pid,attempt+1);return 0;}usleep(100000);}return 5;}}
