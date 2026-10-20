// Local native action/callback oracle. No XPC send, app connection or user input.
#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#import <dispatch/dispatch.h>
#include <dlfcn.h>
#include <string.h>
#include <stdatomic.h>
static _Atomic(unsigned) capturesReleased;
@interface OwnedCapture:NSObject
-(void)observe;
@end
@implementation OwnedCapture
-(void)observe{}
-(void)dealloc{atomic_fetch_add(&capturesReleased,1);[super dealloc];}
@end
static NSInvocation *invoke(id o,NSString *selector,const char *ret,NSArray<NSString*> *types){NSMethodSignature *s=[o methodSignatureForSelector:NSSelectorFromString(selector)];if(!s||strcmp(s.methodReturnType,ret)||s.numberOfArguments!=types.count+2)abort();for(NSUInteger n=0;n<types.count;n++)if(strcmp([s getArgumentTypeAtIndex:n+2],types[n].UTF8String))abort();NSInvocation *i=[NSInvocation invocationWithMethodSignature:s];i.target=o;i.selector=NSSelectorFromString(selector);return i;}
static BOOL boolean(id o,NSString *sel){NSInvocation *i=invoke(o,sel,"B",@[]);[i invoke];BOOL r=NO;[i getReturnValue:&r];return r;}
static id object(id o,NSString *sel){NSInvocation *i=invoke(o,sel,"@",@[]);[i invoke];id r=nil;[i getReturnValue:&r];return r;}
static void send(id action,id response){NSInvocation *i=invoke(action,@"sendResponse:","v",@[@"@"]);[i setArgument:&response atIndex:2];[i invoke];}
static void invalidate(id action){NSInvocation *i=invoke(action,@"invalidate","v",@[]);[i invoke];}
int main(int argc,char **argv){@autoreleasepool{if(argc!=2)return 2;if(!dlopen("/System/Library/PrivateFrameworks/PreviewsServicesUI.framework/Versions/A/PreviewsServicesUI",RTLD_NOW|RTLD_LOCAL))return 3;
 NSString *mode=@(argv[1]);Class actionClass=NSClassFromString(@"BSAction");id action=[actionClass alloc],info=nil;double timeout=.05;dispatch_queue_t queue=dispatch_queue_create("owned.action.reply",DISPATCH_QUEUE_SERIAL);dispatch_semaphore_t arrived=dispatch_semaphore_create(0);NSMutableArray *callbacks=[NSMutableArray array];NSObject *guard=[NSObject new];OwnedCapture *capture=[OwnedCapture new];
 void (^handler)(id)=^(id response){@autoreleasepool{[capture observe];NSError *error=object(response,@"error");NSDictionary *row=@{@"response_class":NSStringFromClass([response class]),@"error_domain":error.domain?:[NSNull null],@"error_code":error?@(error.code):[NSNull null]};@synchronized(guard){[callbacks addObject:row];}dispatch_semaphore_signal(arrived);}};
 NSInvocation *i=invoke(action,@"initWithInfo:timeout:forResponseOnQueue:withHandler:","@",@[@"@",@"d",@"@",@"@?"]);id q=(id)queue;[i setArgument:&info atIndex:2];[i setArgument:&timeout atIndex:3];[i setArgument:&q atIndex:4];[i setArgument:&handler atIndex:5];[i invoke];[i getReturnValue:&action];fprintf(stderr,"initialized\n");if(!action)return 4;[capture release];BOOL before=boolean(action,@"canSendResponse"),valid=boolean(action,@"isValid");
 fprintf(stderr,"state can=%d valid=%d\n",before,valid);id response=[NSClassFromString(@"BSActionResponse") alloc];NSError *error=[mode isEqual:@"error"]?[NSError errorWithDomain:@"Owned.ActionError" code:17 userInfo:nil]:nil;NSInvocation *create=invoke(response,@"initWithInfo:error:","@",@[@"@",@"@"]);[create setArgument:&info atIndex:2];[create setArgument:&error atIndex:3];[create invoke];[create getReturnValue:&response];if(!response)return 5;
 fprintf(stderr,"response ready\n");if([mode isEqual:@"reply"]||[mode isEqual:@"error"]){fprintf(stderr,"send1\n");send(action,response);fprintf(stderr,"after send can=%d valid=%d\n",boolean(action,@"canSendResponse"),boolean(action,@"isValid"));}else if([mode isEqual:@"invalidate"]){invalidate(action);}else if(![mode isEqual:@"timeout"])return 6;
 long wait=dispatch_semaphore_wait(arrived,dispatch_time(DISPATCH_TIME_NOW,500*NSEC_PER_MSEC));BOOL after=boolean(action,@"canSendResponse"),afterValid=boolean(action,@"isValid");
 if([mode isEqual:@"timeout"]&&after){send(action,response);}invalidate(action);dispatch_sync(queue,^{});[NSThread sleepForTimeInterval:.15];dispatch_sync(queue,^{});NSArray *observed=nil;@synchronized(guard){observed=[callbacks copy];}
 [action release];action=nil;dispatch_sync(queue,^{});
 NSData *data=[NSJSONSerialization dataWithJSONObject:@{@"mode":mode,@"owned_handler_capture_deallocations_after_action_release":@(atomic_load(&capturesReleased)),@"can_send_before":@(before),@"valid_before":@(valid),@"callback_arrived_within_500ms":@(wait==0),@"can_send_after_wait":@(after),@"valid_after_wait":@(afterValid),@"callbacks_at_final_queue_barrier":observed,@"post_invalidation_observation_ms":@150,@"external_action_sent":@NO} options:NSJSONWritingPrettyPrinted error:NULL];fwrite(data.bytes,1,data.length,stdout);puts("");[observed release];[response release];[action release];[guard release];dispatch_release(arrived);dispatch_release(queue);return 0;}}
