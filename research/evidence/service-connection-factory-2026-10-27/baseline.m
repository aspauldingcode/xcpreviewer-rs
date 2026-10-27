#import "peer-outgoing.m"
int main(int argc,char**argv){@autoreleasepool{
 xpc_connection_t c=(__bridge_transfer xpc_connection_t)owned_create_client();dispatch_semaphore_t done=dispatch_semaphore_create(0);__block int count=0;__block BOOL ok=NO;
 xpc_connection_set_event_handler(c,^(xpc_object_t e){});xpc_connection_activate(c);
 xpc_object_t d=xpc_dictionary_create(NULL,NULL,0);xpc_dictionary_set_data(d,"data","owned",5);
 xpc_connection_send_message_with_reply(c,d,queue,^(xpc_object_t reply){count++;ok=xpc_get_type(reply)==XPC_TYPE_DICTIONARY;dispatch_semaphore_signal(done);});
 long v=dispatch_semaphore_wait(done,dispatch_time(DISPATCH_TIME_NOW,3*NSEC_PER_SEC));NSDictionary*r=owned_peer_result();NSDictionary*out=@{@"timedOut":@(v!=0),@"callbackCount":@(count),@"dictionaryReply":@(ok),@"peer":r};NSData*b=[NSPropertyListSerialization dataWithPropertyList:out format:NSPropertyListBinaryFormat_v1_0 options:0 error:NULL];[b writeToFile:@(argv[1]) atomically:YES];owned_peer_close();return v||!ok;
}}
