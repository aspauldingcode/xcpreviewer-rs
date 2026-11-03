#include <assert.h>
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <dispatch/dispatch.h>
extern void *canvas_fixture_new(void);
extern int32_t canvas_fixture_fd(void *);
extern void canvas_fixture_retain(void *),canvas_fixture_release(void *);
extern unsigned owned_image_count(void);
extern const char *owned_image_path(unsigned);
extern const unsigned char *owned_image_uuid(unsigned);
extern const char *owned_symbol_path(void *);
static int closed(int fd){errno=0;return fcntl(fd,F_GETFD)==-1&&errno==EBADF;}
int main(void){
 void *(*init)(void*,void*)=dlsym(RTLD_DEFAULT,"swift_unknownObjectWeakInit");
 void *(*load)(void*)=dlsym(RTLD_DEFAULT,"swift_unknownObjectWeakLoadStrong");
 void (*destroy)(void*)=dlsym(RTLD_DEFAULT,"swift_unknownObjectWeakDestroy");
 void (*release)(void*)=dlsym(RTLD_DEFAULT,"swift_unknownObjectRelease");
 assert(init&&load&&destroy&&release&&sizeof(void*)==8);
 const char *path=owned_symbol_path(init);const unsigned char *uuid=0;
 for(unsigned i=0;i<owned_image_count();i++)if(strcmp(path,owned_image_path(i))==0)uuid=owned_image_uuid(i);
 assert(uuid);printf("{\"event\":\"runtime\",\"path\":\"%s\",\"uuid\":\"",path);
 for(int i=0;i<16;i++)printf("%02x",uuid[i]);printf("\",\"slot_size\":8,\"main_queue_export_matches\":%s}\n",dlsym(RTLD_DEFAULT,"_dispatch_main_q")==dispatch_get_main_queue()?"true":"false");
 for(int mode=0;mode<3;mode++){
  void *object=canvas_fixture_new();int fd=canvas_fixture_fd(object);void *slot=0;
  assert(init(&slot,object)==&slot);void *strong=load(&slot);assert(strong==object);release(strong);assert(!closed(fd));
  if(mode==1){canvas_fixture_retain(object);canvas_fixture_release(object);strong=load(&slot);assert(strong==object&&!closed(fd));release(strong);}
  if(mode==2){destroy(&slot);assert(!closed(fd));canvas_fixture_release(object);assert(closed(fd));}
  else {canvas_fixture_release(object);assert(load(&slot)==0&&closed(fd));destroy(&slot);}
  printf("{\"event\":\"control\",\"mode\":%d,\"passed\":true,\"fd_closed\":true}\n",mode);
 }
}
