#import <Foundation/Foundation.h>
#include <xpc/xpc.h>
#include <stdatomic.h>
#include <mach/mach_time.h>
#include <mach-o/loader.h>
#include <dlfcn.h>
#include <pthread.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <assert.h>
static NSLock *traceLock;static NSMutableArray *trace;static unsigned sequence;
static mach_timebase_info_data_t timebase;static _Atomic int drops;static dispatch_semaphore_t freed;
static void event(NSString *name,NSDictionary *fields){[traceLock lock];NSMutableDictionary *v=[NSMutableDictionary dictionaryWithDictionary:fields?:@{}];v[@"event"]=name;v[@"seq"]=@(++sequence);v[@"thread_id"]=@(pthread_mach_thread_np(pthread_self()));v[@"time_ns"]=@((uint64_t)((__uint128_t)mach_absolute_time()*timebase.numer/timebase.denom));[trace addObject:v];NSData *line=[NSJSONSerialization dataWithJSONObject:v options:NSJSONWritingSortedKeys error:NULL];fwrite(line.bytes,1,line.length,stdout);putchar(10);fflush(stdout);[traceLock unlock];}
static BOOL waitFor(dispatch_semaphore_t s,int ms){return dispatch_semaphore_wait(s,dispatch_time(DISPATCH_TIME_NOW,(int64_t)ms*NSEC_PER_MSEC))==0;}
static BOOL closed(int fd){errno=0;return fcntl(fd,F_GETFD)==-1&&errno==EBADF;}
@interface OwnedCapture:NSObject { @public int descriptor; }
-(int)touch;
@end
@implementation OwnedCapture
-(id)init{if((self=[super init])){descriptor=open("/dev/null",O_RDONLY);assert(descriptor>=0);event(@"capture-created",@{@"fd":@(descriptor)});}return self;}
-(int)touch{return fcntl(descriptor,F_GETFD)>=0?17:-1;}
-(void)dealloc{int rc=close(descriptor);atomic_fetch_add(&drops,1);event(@"capture-deinit",@{@"fd":@(descriptor),@"close_result":@(rc)});dispatch_semaphore_signal(freed);[super dealloc];}
@end
static NSDictionary *imageFor(const void *function){Dl_info info={0};if(!dladdr(function,&info)||!info.dli_fbase)return @{};const struct mach_header_64 *h=info.dli_fbase;if(h->magic!=MH_MAGIC_64||h->ncmds>4096||h->sizeofcmds>1024*1024)return @{};const uint8_t *cursor=(const uint8_t *)(h+1),*end=cursor+h->sizeofcmds;NSString *uuid=@"";for(uint32_t i=0;i<h->ncmds;i++){if(cursor+sizeof(struct load_command)>end)break;const struct load_command *lc=(const struct load_command *)cursor;if(lc->cmdsize<sizeof(*lc)||cursor+lc->cmdsize>end)break;if(lc->cmd==LC_UUID&&lc->cmdsize>=sizeof(struct uuid_command)){const struct uuid_command *u=(const struct uuid_command *)lc;NSMutableString *text=[NSMutableString string];for(int j=0;j<16;j++)[text appendFormat:@"%02x",u->uuid[j]];uuid=text;break;}cursor+=lc->cmdsize;}return @{@"path":@(info.dli_fname),@"uuid":uuid};}
int main(int argc,const char **argv){@autoreleasepool{
 alarm(6);if(argc!=2)return 2;BOOL releaseOwner=strcmp(argv[1],"release-inflight")==0||strcmp(argv[1],"release-pending")==0;BOOL cancel=strcmp(argv[1],"cancel-inflight")==0||strcmp(argv[1],"release-inflight")==0,pending=strcmp(argv[1],"cancel-pending")==0||strcmp(argv[1],"release-pending")==0;if(!cancel&&!pending&&strcmp(argv[1],"normal"))return 2;
 mach_timebase_info(&timebase);traceLock=[[NSLock alloc]init];trace=[[NSMutableArray alloc]init];
 NSDictionary *identity=imageFor((const void *)xpc_connection_cancel);assert([identity[@"path"] isEqual:@"/usr/lib/system/libxpc.dylib"]&&[identity[@"uuid"] isEqual:@"c40fcae87a173d8287cb3da4802adef1"]);
 dispatch_queue_t queue=dispatch_queue_create("owned.inflight.reply",DISPATCH_QUEUE_SERIAL);static char key;dispatch_queue_set_specific(queue,&key,&key,NULL);
 dispatch_semaphore_t received=dispatch_semaphore_create(0),entered=dispatch_semaphore_create(0),unblock=dispatch_semaphore_create(0),completed=dispatch_semaphore_create(0),invalid=dispatch_semaphore_create(0);freed=dispatch_semaphore_create(0);
 __block pid_t peerPID=0;__block xpc_connection_t peer=NULL;__block xpc_object_t held=NULL;__block int callbacks=0,invalidations=0,badQueue=0;__block BOOL dictionaryBefore=NO,markerBefore=NO,markerAfter=NO,invalidBefore=NO,invalidAfter=NO;
 xpc_connection_t listener=xpc_connection_create(NULL,queue);assert(listener);
 xpc_connection_set_event_handler(listener,^(xpc_object_t connection){@autoreleasepool{if(xpc_get_type(connection)!=XPC_TYPE_CONNECTION)return;peer=(xpc_connection_t)connection;peerPID=xpc_connection_get_pid(peer);assert(peerPID==getpid());xpc_retain(peer);xpc_connection_set_event_handler(peer,^(xpc_object_t message){@autoreleasepool{if(xpc_get_type(message)!=XPC_TYPE_DICTIONARY)return;const char *kind=xpc_dictionary_get_string(message,"owned.kind");assert(kind&&strcmp(kind,"inflight")==0);assert(!held);held=xpc_dictionary_create_reply(message);assert(held);event(@"peer-request",nil);dispatch_semaphore_signal(received);}});xpc_connection_activate(peer);}});
 xpc_connection_activate(listener);xpc_endpoint_t endpoint=xpc_endpoint_create(listener);assert(endpoint);xpc_connection_t client=xpc_connection_create_from_endpoint(endpoint);xpc_release(endpoint);assert(client);
 xpc_connection_set_target_queue(client,queue);xpc_connection_set_event_handler(client,^(xpc_object_t value){@autoreleasepool{if(value==XPC_ERROR_CONNECTION_INVALID){invalidations++;badQueue+=dispatch_get_specific(&key)!=&key;event(@"client-invalid",nil);dispatch_semaphore_signal(invalid);}}});xpc_connection_activate(client);
 OwnedCapture *token=[[OwnedCapture alloc]init];int fd=token->descriptor;xpc_object_t request=xpc_dictionary_create(NULL,NULL,0);xpc_dictionary_set_string(request,"owned.kind","inflight");
 xpc_connection_send_message_with_reply(client,request,queue,^(xpc_object_t reply){@autoreleasepool{
  callbacks++;badQueue+=dispatch_get_specific(&key)!=&key;assert([token touch]==17);dictionaryBefore=xpc_get_type(reply)==XPC_TYPE_DICTIONARY;const char *marker=dictionaryBefore?xpc_dictionary_get_string(reply,"owned.marker"):NULL;markerBefore=marker&&strcmp(marker,"inflight marker")==0;invalidBefore=reply==XPC_ERROR_CONNECTION_INVALID;assert(pending?invalidBefore:(dictionaryBefore&&markerBefore));
  event(@"callback-blocked",@{@"capture_fd_open":@(!closed(fd))});dispatch_semaphore_signal(entered);assert(waitFor(unblock,2000));
  marker=dictionaryBefore?xpc_dictionary_get_string(reply,"owned.marker"):NULL;markerAfter=marker&&strcmp(marker,"inflight marker")==0;invalidAfter=reply==XPC_ERROR_CONNECTION_INVALID;assert((pending?invalidAfter:markerAfter)&&[token touch]==17);event(@"callback-returning",@{@"reply_valid":@(pending?invalidAfter:markerAfter),@"capture_fd_open":@(!closed(fd))});dispatch_semaphore_signal(completed);
 }});
 xpc_release(request);[token release];assert(waitFor(received,1500));pid_t serverPID=xpc_connection_get_pid(client);event(@"client-peer-query",@{@"reported_pid":@(serverPID),@"accepted_peer_pid":@(peerPID)});if(pending){event(@"pending-cancel-begin",nil);xpc_connection_cancel(client);event(@"pending-cancel-returned",nil);}else{dispatch_sync(queue,^{event(@"peer-reply-submit",nil);xpc_dictionary_set_string(held,"owned.marker","inflight marker");xpc_connection_send_message(peer,held);xpc_release(held);held=NULL;});}assert(waitFor(entered,1500));
 assert(atomic_load(&drops)==0&&!closed(fd));event(@"main-observed-blocked",@{@"capture_drops":@(atomic_load(&drops)),@"capture_fd_open":@(!closed(fd))});
 if(cancel){event(@"cancel-begin",nil);xpc_connection_cancel(client);event(@"cancel-returned-blocked",@{@"capture_drops":@(atomic_load(&drops)),@"capture_fd_open":@(!closed(fd))});assert(atomic_load(&drops)==0&&!closed(fd));}
 if(releaseOwner){event(@"client-owner-release-begin",nil);xpc_release(client);client=NULL;event(@"client-owner-release-returned-blocked",@{@"capture_drops":@(atomic_load(&drops)),@"capture_fd_open":@(!closed(fd))});assert(atomic_load(&drops)==0&&!closed(fd));}
 event(@"callback-release-signal",nil);dispatch_semaphore_signal(unblock);assert(waitFor(completed,1500));assert(waitFor(freed,1000));assert(atomic_load(&drops)==1&&closed(fd));event(@"capture-cleanup-observed",@{@"capture_drops":@(atomic_load(&drops)),@"fd_closed":@(closed(fd))});
 if(!cancel&&!pending){event(@"cancel-after-callback",nil);xpc_connection_cancel(client);}BOOL gotInvalid=waitFor(invalid,1000);if(!releaseOwner)assert(gotInvalid);if(pending)dispatch_sync(queue,^{event(@"late-peer-reply-submit",nil);xpc_dictionary_set_string(held,"owned.marker","inflight marker");xpc_connection_send_message(peer,held);xpc_release(held);held=NULL;});
 dispatch_semaphore_t quiet=dispatch_semaphore_create(0);dispatch_after(dispatch_time(DISPATCH_TIME_NOW,100*NSEC_PER_MSEC),queue,^{dispatch_semaphore_signal(quiet);});assert(waitFor(quiet,500));dispatch_sync(queue,^{});
 assert(callbacks==1&&(releaseOwner?invalidations<=1:invalidations==1)&&badQueue==0&&(pending?(invalidBefore&&invalidAfter):dictionaryBefore&&markerBefore&&markerAfter));event(@"observation-complete",nil);
 NSDictionary *result=@{@"mode":@(argv[1]),@"pid":@(getpid()),@"peer_pid":@(peerPID),@"server_pid":@(serverPID),@"runtime":identity,@"callbacks":@(callbacks),@"invalid_events":@(invalidations),@"invalid_event_observed":@(gotInvalid),@"caller_client_reference_released_while_blocked":@(releaseOwner),@"queue_mismatches":@(badQueue),@"capture_drops":@(atomic_load(&drops)),@"fd_closed":@(closed(fd)),@"dictionary_before":@(dictionaryBefore),@"invalid_before":@(invalidBefore),@"invalid_after":@(invalidAfter),@"marker_before":@(markerBefore),@"marker_after":@(markerAfter),@"quiet_window_ms":@100,@"private_canvas_invoked":@NO,@"target_resource_settlement_verified":@NO,@"trace":trace};
 NSData *json=[NSJSONSerialization dataWithJSONObject:result options:NSJSONWritingSortedKeys error:NULL];fwrite(json.bytes,1,json.length,stdout);putchar('\n');
 dispatch_sync(queue,^{if(held){xpc_release(held);held=NULL;}if(peer)xpc_connection_cancel(peer);});xpc_connection_cancel(listener);if(client)xpc_release(client);dispatch_sync(queue,^{if(peer){xpc_release(peer);peer=NULL;}});xpc_release(listener);return 0;
}}
