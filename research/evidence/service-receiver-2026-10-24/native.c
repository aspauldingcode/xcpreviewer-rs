#include <xpc/xpc.h>
#include <dispatch/dispatch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *f = fopen(argv[1], "rb"); if (!f) return 3;
    unsigned char bytes[4096]; size_t n = fread(bytes, 1, sizeof(bytes), f); fclose(f); if (!n || n == sizeof(bytes)) return 4;
    const unsigned char *expected_bytes = bytes;
    xpc_object_t plain = xpc_dictionary_create(NULL,NULL,0);
    xpc_dictionary_set_data(plain,"data",bytes,n);
    xpc_object_t impossible = xpc_dictionary_create_reply(plain);
    int plain_reply = impossible != NULL; if (impossible) xpc_release(impossible); xpc_release(plain);
    dispatch_queue_t q = dispatch_queue_create("owned.receiver.control",DISPATCH_QUEUE_SERIAL);
    dispatch_group_t group = dispatch_group_create(); dispatch_group_enter(group); dispatch_group_enter(group);
    __block xpc_connection_t peer = NULL;
    __block int one_way = -1, request = -1, callback = 0, equal = 1, errors = 0;
    xpc_connection_t listener = xpc_connection_create(NULL,q); if (!listener) return 5;
    xpc_connection_set_event_handler(listener, ^(xpc_object_t incoming) {
        if (xpc_get_type(incoming) != XPC_TYPE_CONNECTION) { errors++; return; }
        peer = (xpc_connection_t)incoming; xpc_retain(peer);
        xpc_connection_set_event_handler(peer, ^(xpc_object_t message) {
            if (xpc_get_type(message) != XPC_TYPE_DICTIONARY) { errors++; return; }
            const char *mode = xpc_dictionary_get_string(message,"owned.mode");
            size_t got = 0; const void *data = xpc_dictionary_get_data(message,"data",&got);
            equal &= got == n && data && memcmp(data,expected_bytes,n) == 0;
            xpc_object_t reply = xpc_dictionary_create_reply(message);
            if (mode && strcmp(mode,"one-way") == 0) { one_way = reply != NULL; dispatch_group_leave(group); }
            if (mode && strcmp(mode,"request") == 0) request = reply != NULL;
            if (reply) {xpc_dictionary_set_bool(reply,"owned.accepted",true); xpc_connection_send_message(peer,reply); xpc_release(reply);}
        });
        xpc_connection_activate(peer);
    });
    xpc_connection_activate(listener);
    xpc_endpoint_t endpoint = xpc_endpoint_create(listener); if (!endpoint) return 6;
    xpc_connection_t client = xpc_connection_create_from_endpoint(endpoint); xpc_release(endpoint);
    if (!client) return 7;
    xpc_connection_set_event_handler(client, ^(xpc_object_t event) {if (xpc_get_type(event) == XPC_TYPE_ERROR) errors++;});
    xpc_connection_activate(client);
    for (int i=0; i<2; i++) {
        xpc_object_t message = xpc_dictionary_create(NULL,NULL,0);
        xpc_dictionary_set_string(message,"owned.mode",i ? "request" : "one-way");
        xpc_dictionary_set_data(message,"data",bytes,n);
        if (!i) xpc_connection_send_message(client,message);
        else xpc_connection_send_message_with_reply(client,message,q,^(xpc_object_t reply) {
            callback = xpc_get_type(reply) == XPC_TYPE_DICTIONARY && xpc_dictionary_get_bool(reply,"owned.accepted");
            dispatch_group_leave(group);
        });
        xpc_release(message);
    }
    long timed_out = dispatch_group_wait(group,dispatch_time(DISPATCH_TIME_NOW,3*NSEC_PER_SEC));
    // Read callback fields on their serial queue after group completion.
    __block int failed = 1;
    dispatch_sync(q, ^{
        failed = plain_reply || one_way != 0 || request != 1 || !callback || !equal || errors;
        printf("{\"plain_reply\":%s,\"one_way_reply\":%d,\"request_reply\":%d,\"reply_callback_accepted\":%d,\"wire_bytes_equal\":%d,\"wire_length\":%zu,\"errors_before_cleanup\":%d,\"timed_out\":%s}\n",plain_reply?"true":"false",one_way,request,callback,equal,n,errors,timed_out?"true":"false");
    });
    xpc_connection_cancel(client); if (peer) xpc_connection_cancel(peer); xpc_connection_cancel(listener);
    // Process exit is not evidence that native rights/resources are settled.
    return timed_out ? 8 : (failed ? 9 : 0);
}
