#include <sys/types.h>
#include <sys/wait.h>
#include <sys/select.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <stdint.h>
#include <mach-o/dyld.h>
static int readbyte(int fd,char expected) {
 fd_set set;FD_ZERO(&set);FD_SET(fd,&set);struct timeval t={4,0};char c;
 return select(fd+1,&set,NULL,NULL,&t)==1 && read(fd,&c,1)==1 && c==expected;
}
int main(int argc,char **argv) {
 if(argc!=2)return 2;
 int ready[2],go[2];if(pipe(ready)||pipe(go))return 3;
 pid_t child=fork();if(child<0)return 4;
 if(child==0){close(ready[0]);close(go[1]);if(setsid()<0)_exit(41);if(write(ready[1],"r",1)!=1)_exit(41);close(ready[1]);
  if(!readbyte(go[0],'g'))_exit(43);close(go[0]);FILE *out=fopen(argv[1],"wb");if(!out)_exit(44);
  for(int i=0;i<32;i++)if(fputc(i,out)==EOF)_exit(45);
  if(fclose(out))_exit(46);_exit(42);
 }
 close(ready[1]);close(go[0]);if(!readbyte(ready[0],'r'))return 5;close(ready[0]);
 char raw[4096],path[PATH_MAX];uint32_t n=sizeof(raw);if(_NSGetExecutablePath(raw,&n)||!realpath(raw,path))return 6;
 printf("{\"phase\":\"ready\",\"pid\":%d,\"parent\":%d,\"group\":%d,\"child\":%d,\"child_group\":%d,\"executable\":\"%s\"}\n",getpid(),getppid(),getpgrp(),child,getpgid(child),path);fflush(stdout);
 if(!readbyte(0,'g')){close(go[1]);waitpid(child,NULL,0);return 7;}
 if(write(go[1],"g",1)!=1)return 8;close(go[1]);siginfo_t info={0};
 if(waitid(P_PID,child,&info,WEXITED|WNOWAIT))return 9;
 printf("{\"phase\":\"unreaped\",\"child\":%d,\"status\":%d,\"code\":%d,\"exited\":%s}\n",info.si_pid,info.si_status,info.si_code,info.si_code==CLD_EXITED?"true":"false");fflush(stdout);
 if(!readbyte(0,'r')){waitpid(child,NULL,0);return 10;}
 int status=0;pid_t waited=waitpid(child,&status,0);
 printf("{\"phase\":\"reaped\",\"child\":%d,\"exit_code\":%d,\"exited\":%s}\n",waited,WIFEXITED(status)?WEXITSTATUS(status):-1,WIFEXITED(status)?"true":"false");fflush(stdout);
 return waited==child && WIFEXITED(status)&&WEXITSTATUS(status)==42?0:11;
}
