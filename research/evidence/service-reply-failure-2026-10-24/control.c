#include <xpc/xpc.h>
#include <stdio.h>
#include <stdlib.h>
static void observe(const char *name, xpc_object_t object) {
    xpc_type_t type=xpc_get_type(object);
    const char *category = type==XPC_TYPE_DICTIONARY ? "dictionary" : type==XPC_TYPE_ERROR ? "error" : "other";
    const char *event = type!=XPC_TYPE_ERROR ? "none" : xpc_equal(object,(xpc_object_t)XPC_ERROR_CONNECTION_INTERRUPTED) ? "connectionInterrupted" : xpc_equal(object,(xpc_object_t)XPC_ERROR_CONNECTION_INVALID) ? "connectionInvalidated" : xpc_equal(object,(xpc_object_t)XPC_ERROR_TERMINATION_IMMINENT) ? "terminationImminent" : "unknown";
    char *description=xpc_copy_description(object);
    printf("%s\t%s\t%s\t%d\n",name,category,event,description!=NULL);
    free(description);
}
int main(void) {
    observe("interrupted",(xpc_object_t)XPC_ERROR_CONNECTION_INTERRUPTED);
    observe("invalidated",(xpc_object_t)XPC_ERROR_CONNECTION_INVALID);
    observe("termination",(xpc_object_t)XPC_ERROR_TERMINATION_IMMINENT);
    xpc_object_t objects[]={xpc_int64_create(-17),xpc_string_create("owned/stone"),xpc_bool_create(true),xpc_null_create(),xpc_array_create(NULL,0),xpc_dictionary_create(NULL,NULL,0)};
    const char *names[]={"integer","string","boolean","null","array","dictionary"};
    for(size_t i=0;i<6;i++){observe(names[i],objects[i]);xpc_release(objects[i]);}
    return 0;
}
