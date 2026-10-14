#include <sys/event.h>
#include <sys/proc_info.h>
#include <sys/wait.h>
#include <libproc.h>
#include <unistd.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int matches(int pid, uint64_t seconds, uint64_t micros, const char *expected) {
    struct proc_bsdinfo info;
    char path[PROC_PIDPATHINFO_MAXSIZE];
    return proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &info, sizeof info) == sizeof info
        && info.pbi_pid == (uint32_t)pid && info.pbi_start_tvsec == seconds
        && info.pbi_start_tvusec == micros && proc_pidpath(pid, path, sizeof path) > 0
        && strcmp(path, expected) == 0;
}

int main(int argc, char **argv) {
    if (argc != 5) return 90;
    int pid = atoi(argv[1]);
    uint64_t seconds = strtoull(argv[2], NULL, 10);
    uint64_t micros = strtoull(argv[3], NULL, 10);
    if (pid <= 0 || !matches(pid, seconds, micros, argv[4])) return 94;
    int queue = kqueue();
    if (queue < 0) return 96;
    struct kevent change;
    EV_SET(&change, pid, EVFILT_PROC, EV_ADD | EV_ENABLE | EV_ONESHOT,
        NOTE_EXIT | NOTE_EXITSTATUS, 0, NULL);
    if (kevent(queue, &change, 1, NULL, 0, NULL)) return 97;
    if (!matches(pid, seconds, micros, argv[4])) return 94;
    printf("{\"registered\":true,\"pid\":%d,\"seconds\":%llu,\"micros\":%llu}\n",
        pid, (unsigned long long)seconds, (unsigned long long)micros);
    fflush(stdout);
    struct timespec deadline = {4, 0};
    struct kevent event;
    int count = kevent(queue, NULL, 0, &event, 1, &deadline);
    if (count != 1) return 100;
    if (event.ident != (uintptr_t)pid || event.filter != EVFILT_PROC
        || (event.flags & EV_ERROR) || !(event.fflags & NOTE_EXIT)) return 99;
    int status = (int)event.data;
    printf("{\"pid\":%d,\"raw_status\":%d,\"exited\":%s,\"exit_code\":%d,\"flags\":%u,\"fflags\":%u}\n",
        pid, status, WIFEXITED(status) ? "true" : "false",
        WIFEXITED(status) ? WEXITSTATUS(status) : -1, event.flags, event.fflags);
    close(queue);
    return 0;
}
