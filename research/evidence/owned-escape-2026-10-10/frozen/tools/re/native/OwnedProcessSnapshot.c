/* Public libproc observation only. No process writes, signals, or argument reads. */
#include <libproc.h>
#include <sys/proc_info.h>
#include <sys/proc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <limits.h>

struct row { int pid, selected; struct proc_bsdinfo b; };
static int info(int pid, struct proc_bsdinfo *b) {
    return proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, b, sizeof(*b)) == sizeof(*b)
        && b->pbi_pid == (uint32_t)pid;
}
static int same(const struct proc_bsdinfo *a, const struct proc_bsdinfo *b) {
    return a->pbi_pid == b->pbi_pid && a->pbi_start_tvsec == b->pbi_start_tvsec
        && a->pbi_start_tvusec == b->pbi_start_tvusec;
}
static void quoted(const char *s) {
    putchar('"');
    for (const unsigned char *p=(const unsigned char *)s; *p; ++p) {
        /* Byte escaping also makes non-ASCII paths safe JSON. */
        if (*p < 32 || *p >= 127) printf("\\u%04x", *p);
        else if (*p == '"' || *p == '\\') { putchar('\\'); putchar(*p); }
        else putchar(*p);
    }
    putchar('"');
}
int main(int argc, char **argv) {
    int needed=proc_listallpids(NULL, 0);
    if (needed <= 0 || needed > 65280) return 2;
    int capacity=needed+256;
    int *pids=calloc(capacity,sizeof(int));
    struct row *rows=calloc(capacity,sizeof(*rows));
    if (!pids || !rows) return 3;
    int n=proc_listallpids(pids,capacity*sizeof(int));
    if (n <= 0 || n >= capacity) return 4;
    int count=0;
    for (int i=0;i<n;++i) if (pids[i]>0 && info(pids[i],&rows[count].b)) {
        rows[count].pid=pids[i]; ++count;
    }
    for (int j=1;j<argc;++j) {
        unsigned long long sec=0,usec=0; int pid=0; char extra;
        int parsed=sscanf(argv[j],"%d:%llu:%llu%c",&pid,&sec,&usec,&extra);
        if ((parsed!=1 && parsed!=3) || pid<=0) return 5;
        for (int i=0;i<count;++i) if (rows[i].pid==pid && (parsed==1 ||
            (rows[i].b.pbi_start_tvsec==sec && rows[i].b.pbi_start_tvusec==usec))) rows[i].selected=1;
    }
    int changed;
    do {
        changed=0;
        for (int i=0;i<count;++i) if (!rows[i].selected)
            for (int j=0;j<count;++j) if (rows[j].selected && rows[i].b.pbi_ppid==(uint32_t)rows[j].pid) {
                rows[i].selected=1; changed=1; break;
            }
    } while (changed);
    printf("["); int first=1;
    for (int i=0;i<count;++i) if (rows[i].selected) {
        struct proc_bsdinfo before,after; char path[PROC_PIDPATHINFO_MAXSIZE]={0};
        if (!info(rows[i].pid,&before) || !same(&before,&rows[i].b)) continue;
        int length=proc_pidpath(rows[i].pid,path,sizeof(path));
        if (length<=0 || length>=(int)sizeof(path) || !memchr(path,0,sizeof(path))) {
            /* Missing identity for a still-live candidate is an observation
               failure, not evidence of exit. Zombies are not live writers. */
            if (info(rows[i].pid,&after) && same(&before,&after) && after.pbi_status!=SZOMB) return 6;
            continue;
        }
        if (!info(rows[i].pid,&after) || !same(&before,&after)) continue;
        if (!first) putchar(','); first=0;
        printf("{\"pid\":%d,\"parent\":%u,\"group\":%u,\"state\":\"%s\",\"identity\":[%llu,%llu,",
            rows[i].pid,after.pbi_ppid,after.pbi_pgid,after.pbi_status==SZOMB ? "Z" : "L",
            (unsigned long long)after.pbi_start_tvsec,(unsigned long long)after.pbi_start_tvusec);
        quoted(path); printf("]}");
    }
    puts("]"); free(rows); free(pids); return 0;
}
