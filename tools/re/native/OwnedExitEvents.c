/* Owned process exit-event observer. No signals. The caller pins both births. */
#include <sys/event.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <sys/proc_info.h>
#include <libproc.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <errno.h>
static double mono(void){struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))exit(91);return t.tv_sec+t.tv_nsec/1e9;}
static FILE *file(const char *root,const char *name){char p[4096];int n=snprintf(p,sizeof p,"%s/%s",root,name);if(n<0||n>=(int)sizeof p)exit(92);FILE*f=fopen(p,"w");if(!f)exit(93);return f;}
static void identity(int pid,uint64_t sec,uint64_t usec,const char*expected){struct proc_bsdinfo b;char path[PROC_PIDPATHINFO_MAXSIZE];if(proc_pidinfo(pid,PROC_PIDTBSDINFO,0,&b,sizeof b)!=sizeof b||b.pbi_pid!=(uint32_t)pid||b.pbi_start_tvsec!=sec||b.pbi_start_tvusec!=usec||proc_pidpath(pid,path,sizeof path)<=0||strcmp(path,expected))exit(94);}
int main(int argc,char**argv){if(argc!=10)return 90;const char*root=argv[1];int pid[2]={atoi(argv[2]),atoi(argv[6])};uint64_t sec[2]={strtoull(argv[3],0,10),strtoull(argv[7],0,10)},usec[2]={strtoull(argv[4],0,10),strtoull(argv[8],0,10)};const char*paths[2]={argv[5],argv[9]};if(pid[0]<=0||pid[1]<=0||pid[0]==pid[1])return 95;int kq=kqueue();if(kq<0)return 96;struct kevent changes[2];for(int i=0;i<2;i++){identity(pid[i],sec[i],usec[i],paths[i]);EV_SET(&changes[i],pid[i],EVFILT_PROC,EV_ADD|EV_ENABLE|EV_ONESHOT,NOTE_EXIT|NOTE_EXITSTATUS,0,0);}if(kevent(kq,changes,2,0,0,0))return 97;for(int i=0;i<2;i++)identity(pid[i],sec[i],usec[i],paths[i]);FILE*f=file(root,"registered.json");fprintf(f,"{\"root_pid\":%d,\"child_pid\":%d,\"note_exit\":%u,\"note_exitstatus\":%u,\"birth_rechecked\":true}",pid[0],pid[1],NOTE_EXIT,NOTE_EXITSTATUS);fclose(f);f=file(root,"finish");fputs("exit",f);fclose(f);double deadline=mono()+4;int count=0,seen[2]={0,0};f=file(root,"kernel-exit-events.json");fputs("[",f);while(count<2&&mono()<deadline){struct timespec timeout={0,100000000};struct kevent event;int n=kevent(kq,0,0,&event,1,&timeout);if(n<0){if(errno==EINTR)continue;return 98;}if(!n)continue;int i=event.ident==(uintptr_t)pid[0]?0:event.ident==(uintptr_t)pid[1]?1:-1;if(i<0||seen[i]||event.filter!=EVFILT_PROC||(event.flags&EV_ERROR)||!(event.fflags&NOTE_EXIT))return 99;seen[i]=1;int status=(int)event.data;fprintf(f,"%s{\"pid\":%d,\"filter\":%d,\"flags\":%u,\"fflags\":%u,\"data\":%lld,\"exited\":%s,\"exit_code\":%d}",count?",":"",pid[i],event.filter,event.flags,event.fflags,(long long)event.data,WIFEXITED(status)?"true":"false",WIFEXITED(status)?WEXITSTATUS(status):-1);fflush(f);count++;}fputs("]",f);fclose(f);close(kq);return count==2?0:100;}
