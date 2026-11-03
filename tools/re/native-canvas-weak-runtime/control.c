#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <objc/runtime.h>
extern void *canvas_fixture_new(void);
extern int32_t canvas_fixture_fd(void *);
extern void canvas_fixture_retain(void *),canvas_fixture_release(void *);
extern void *canvas_weak_new(void *);
extern int32_t canvas_weak_alive(void *);
extern void canvas_weak_dispose(void *);
static int closed(int fd) {errno=0;return fcntl(fd,F_GETFD)==-1 && errno==EBADF;}
int main(void) {
 for(int mode=0;mode<3;mode++) {
  void *object=canvas_fixture_new();int fd=canvas_fixture_fd(object);
  assert(strstr(object_getClassName((id)object),"Fixture")!=NULL);
  void *weak=canvas_weak_new(object);assert(canvas_weak_alive(weak)==1 && !closed(fd));
  if(mode==1) {canvas_fixture_retain(object);canvas_fixture_release(object);assert(canvas_weak_alive(weak)==1 && !closed(fd));}
  if(mode==2) {canvas_weak_dispose(weak);assert(!closed(fd));canvas_fixture_release(object);assert(closed(fd));}
  else {canvas_fixture_release(object);assert(canvas_weak_alive(weak)==0 && closed(fd));canvas_weak_dispose(weak);}
  printf("{\"control\":%d,\"passed\":true,\"owned_fd_closed\":true}\n",mode);
 }
}
