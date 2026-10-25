#import <Foundation/Foundation.h>
#include <xpc/xpc.h>
#include <stdatomic.h>
#include <dlfcn.h>
#include <mach-o/loader.h>
static _Atomic int drops=0;
static dispatch_semaphore_t freed;
@interface OwnedCapture:NSObject
-(int)touch;
@end
@implementation OwnedCapture
-(int)touch{return 17;}
-(void)dealloc{atomic_fetch_add(&drops,1);dispatch_semaphore_signal(freed);[super dealloc];}
@end
static BOOL waitFor(dispatch_semaphore_t s,int ms){return dispatch_semaphore_wait(s,dispatch_time(DISPATCH_TIME_NOW,(int64_t)ms*NSEC_PER_MSEC))==0;}
static NSDictionary *imageFor(const void *function){Dl_info info={0};if(!dladdr(function,&info)||!info.dli_fbase)return @{};const struct mach_header_64 *h=info.dli_fbase;if(h->magic!=MH_MAGIC_64||h->ncmds>4096||h->sizeofcmds>1024*1024)return @{};const uint8_t *cursor=(const uint8_t *)(h+1),*end=cursor+h->sizeofcmds;NSString *uuid=@"";for(uint32_t i=0;i<h->ncmds;i++){if(cursor+sizeof(struct load_command)>end)break;const struct load_command *lc=(const struct load_command *)cursor;if(lc->cmdsize<sizeof(*lc)||cursor+lc->cmdsize>end)break;if(lc->cmd==LC_UUID&&lc->cmdsize>=sizeof(struct uuid_command)){const struct uuid_command *u=(const struct uuid_command *)lc;NSMutableString *text=[NSMutableString string];for(int j=0;j<16;j++)[text appendFormat:@"%02x",u->uuid[j]];uuid=text;break;}cursor+=lc->cmdsize;}return @{@"path":@(info.dli_fname),@"uuid":uuid};}
int main(int argc,const char **argv){@autoreleasepool{
 if(argc!=2)return 1;BOOL cancel=strcmp(argv[1],"cancel")==0;if(!cancel&&strcmp(argv[1],"normal"))return 2;
 dispatch_queue_t queue=dispatch_queue_create("owned.cancel.reply",DISPATCH_QUEUE_SERIAL);static char key;dispatch_queue_set_specific(queue,&key,&key,NULL);
 dispatch_semaphore_t received=dispatch_semaphore_create(0),completed=dispatch_semaphore_create(0),invalid=dispatch_semaphore_create(0);freed=dispatch_semaphore_create(0);
 NSMutableArray *trace=[NSMutableArray array];__block xpc_connection_t peer=NULL;__block xpc_object_t held=NULL;__block int callbacks=0,requests=0,invalidations=0,badQueue=0,exceptions=0;__block BOOL dictionary=NO,replyInvalid=NO,markerMatches=NO;
 xpc_connection_t listener=xpc_connection_create(NULL,queue);if(!listener)return 3;
 xpc_connection_set_event_handler(listener,^(xpc_object_t event){@autoreleasepool{if(xpc_get_type(event)!=XPC_TYPE_CONNECTION)return;peer=(xpc_connection_t)event;xpc_retain(peer);xpc_connection_set_event_handler(peer,^(xpc_object_t message){@autoreleasepool{if(xpc_get_type(message)!=XPC_TYPE_DICTIONARY)return;requests++;held=xpc_dictionary_create_reply(message);[trace addObject:@"peer.request.gated"];dispatch_semaphore_signal(received);}});xpc_connection_activate(peer);}});
 xpc_connection_activate(listener);xpc_endpoint_t endpoint=xpc_endpoint_create(listener);if(!endpoint)return 4;xpc_connection_t client=xpc_connection_create_from_endpoint(endpoint);xpc_release(endpoint);if(!client)return 5;
 xpc_connection_set_target_queue(client,queue);xpc_connection_set_event_handler(client,^(xpc_object_t event){@autoreleasepool{if(event==XPC_ERROR_CONNECTION_INVALID){invalidations++;[trace addObject:@"client.invalid"];dispatch_semaphore_signal(invalid);}}});xpc_connection_activate(client);
 OwnedCapture *token=[[OwnedCapture alloc]init];xpc_object_t request=xpc_dictionary_create(NULL,NULL,0);xpc_dictionary_set_string(request,"owned.kind","gated");
 xpc_connection_send_message_with_reply(client,request,queue,^(xpc_object_t reply){@autoreleasepool{@try{callbacks++;badQueue+=dispatch_get_specific(&key)!=&key;if([token touch]!=17)exceptions++;dictionary=xpc_get_type(reply)==XPC_TYPE_DICTIONARY;replyInvalid=reply==XPC_ERROR_CONNECTION_INVALID;const char *marker=dictionary?xpc_dictionary_get_string(reply,"owned.marker"):NULL;markerMatches=marker&&strcmp(marker,"owned reply marker")==0;[trace addObject:dictionary?@"reply.dictionary":(replyInvalid?@"reply.invalid":@"reply.other")];}@catch(NSException *e){exceptions++;}dispatch_semaphore_signal(completed);}});
 xpc_release(request);[token release];BOOL gotRequest=waitFor(received,1500);__block BOOL before=NO;
 dispatch_sync(queue,^{before=atomic_load(&drops)==0;[trace addObject:@"capture.before.operation"];});
 if(!gotRequest)return 6;
 if(cancel){dispatch_sync(queue,^{[trace addObject:@"cancel.request"];});xpc_connection_cancel(client);}else{dispatch_sync(queue,^{if(held){xpc_dictionary_set_string(held,"owned.marker","owned reply marker");[trace addObject:@"peer.reply.submit"];xpc_connection_send_message(peer,held);xpc_release(held);held=NULL;}});}
 BOOL gotCallback=waitFor(completed,1500);BOOL droppedAfterCallback=waitFor(freed,1000);
 __block BOOL lateSubmitted=NO;
 if(cancel){dispatch_sync(queue,^{if(held){xpc_dictionary_set_string(held,"owned.marker","owned reply marker");[trace addObject:@"peer.reply.late.submit"];xpc_connection_send_message(peer,held);xpc_release(held);held=NULL;lateSubmitted=YES;}});}else{xpc_connection_cancel(client);}
 BOOL gotInvalid=waitFor(invalid,1000);dispatch_semaphore_t quiet=dispatch_semaphore_create(0);dispatch_after(dispatch_time(DISPATCH_TIME_NOW,150*NSEC_PER_MSEC),queue,^{dispatch_semaphore_signal(quiet);});BOOL quietFinished=waitFor(quiet,500);
 __block int result=1;dispatch_sync(queue,^{NSDictionary *row=@{@"mode":cancel?@"cancel":@"normal",@"request_received":@(gotRequest),@"requests":@(requests),@"callback_received":@(gotCallback),@"callbacks_in_observation_window":@(callbacks),@"invalid_event_received":@(gotInvalid),@"invalid_events":@(invalidations),@"reply_dictionary":@(dictionary),@"reply_invalid":@(replyInvalid),@"owned_marker_matches":@(markerMatches),@"capture_alive_before_operation":@(before),@"capture_dropped_after_callback_within_1s":@(droppedAfterCallback),@"capture_drops":@(atomic_load(&drops)),@"late_peer_reply_submitted":@(lateSubmitted),@"queue_mismatches":@(badQueue),@"exceptions":@(exceptions),@"quiet_window_completed":@(quietFinished),@"quiet_window_ms":@150,@"trace":trace,@"cancel_image":imageFor((const void *)xpc_connection_cancel),@"reply_image":imageFor((const void *)xpc_connection_send_message_with_reply),@"os_version":[NSProcessInfo processInfo].operatingSystemVersionString,@"private_connection_invoked":@NO,@"target_resource_settlement_proven":@NO};NSData *data=[NSJSONSerialization dataWithJSONObject:row options:NSJSONWritingSortedKeys error:NULL];fwrite(data.bytes,1,data.length,stdout);putchar('\n');result=!(gotRequest&&gotCallback&&gotInvalid&&quietFinished&&before&&callbacks==1&&requests==1&&!badQueue&&!exceptions&&(cancel?(replyInvalid&&lateSubmitted):markerMatches));});
 // Cancel and release only objects created in this process. These SDK calls
 // and helper exit do not establish global rights or native target settlement.
 dispatch_sync(queue,^{if(held){xpc_release(held);held=NULL;}if(peer)xpc_connection_cancel(peer);});xpc_connection_cancel(listener);xpc_release(client);dispatch_sync(queue,^{if(peer){xpc_release(peer);peer=NULL;}});xpc_release(listener);
 return result?7:0;
}}
