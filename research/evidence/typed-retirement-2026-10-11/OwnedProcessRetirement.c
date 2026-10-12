/* Public, read-only lifetime/state query. No executable-path synthesis. */
#include <libproc.h>
#include <sys/proc_info.h>
#include <sys/proc.h>
#include <stdio.h>
#include <stdint.h>
static int info(int pid,struct proc_bsdinfo *b){return proc_pidinfo(pid,PROC_PIDTBSDINFO,0,b,sizeof(*b))==sizeof(*b)&&b->pbi_pid==(uint32_t)pid;}
static int same(struct proc_bsdinfo *a,struct proc_bsdinfo *b){return a->pbi_pid==b->pbi_pid&&a->pbi_start_tvsec==b->pbi_start_tvsec&&a->pbi_start_tvusec==b->pbi_start_tvusec;}
int main(int argc,char **argv){
 if(argc<2||argc>1025)return 2;
 printf("[");
 for(int i=1;i<argc;i++){
  int pid=0;unsigned long long sec=0,usec=0;char extra;
  if(sscanf(argv[i],"%d:%llu:%llu%c",&pid,&sec,&usec,&extra)!=3||pid<=0)return 3;
  struct proc_bsdinfo a,b;const char *status="unavailable";int observed=0;
  if(info(pid,&a)&&info(pid,&b)&&same(&a,&b)){
   observed=1;
   status=(b.pbi_start_tvsec!=sec||b.pbi_start_tvusec!=usec)?"reused":b.pbi_status==SZOMB?"retired":"live";
  }
  if(i>1)putchar(',');
  printf("{\"pid\":%d,\"expected_birth\":[%llu,%llu],\"status\":\"%s\",\"observed_birth\":",pid,sec,usec,status);
  if(observed)printf("[%llu,%llu]",(unsigned long long)b.pbi_start_tvsec,(unsigned long long)b.pbi_start_tvusec);else printf("null");
  putchar('}');
 }
 puts("]");return 0;
}
