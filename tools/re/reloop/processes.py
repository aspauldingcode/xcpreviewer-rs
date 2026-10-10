"""Bounded tracking of owned descendants, including children leaving the group."""
import os
import signal
import subprocess
import time


def snapshot():
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,stat=,lstart=,command='],
                            capture_output=True, text=True, check=True, timeout=2)
    rows = {}
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 9)
        if len(parts) == 10:
            pid, parent, group = map(int, parts[:3])
            rows[pid] = {'parent': parent, 'group': group,
                         'state': parts[3], 'identity': tuple(parts[4:9]) + (parts[9],)}
    return rows


class OwnedTree:
    def __init__(self, pid, process=None):
        self.pid = pid
        self.process = process
        self.known = {}

    def observe(self):
        rows = snapshot()
        root_live = self.process is not None and self.process.poll() is None
        owned = {self.pid} if root_live or (self.process is None and self.pid not in self.known) else set()
        # A known identity can still be ours after reparenting or setsid().
        owned.update(pid for pid, identity in self.known.items()
                     if pid in rows and rows[pid]['identity'] == identity)
        while True:
            children = {pid for pid, row in rows.items() if row['parent'] in owned}
            if children <= owned:
                break
            owned.update(children)
        for pid in owned:
            if pid in rows:
                self.known[pid] = rows[pid]['identity']
        return rows

    def drain(self):
        # Never signal a PID just because its numeric value was previously ours.
        for sig in (signal.SIGTERM, signal.SIGKILL):
            rows = self.observe()
            for pid, identity in list(self.known.items()):
                if pid == self.pid or pid not in rows or rows[pid]['identity'] != identity:
                    continue
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    pass
            time.sleep(0.1)
        remaining = self.observe()
        live = [pid for pid, identity in self.known.items() if pid != self.pid and pid in remaining and remaining[pid]['identity'] == identity and not remaining[pid].get('state','').startswith('Z')]
        if live:
            raise RuntimeError('Owned descendants remain live after bounded cleanup')
        return {'tracked_processes': len(self.known),
                'scope': 'Observed owned ancestry plus unchanged ps start-time/command identity; not arbitrary escaped descendants between observations.'}
