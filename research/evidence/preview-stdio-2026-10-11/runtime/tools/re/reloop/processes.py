"""Bounded tracking of owned descendants, including children leaving the group."""
import os
import signal
import subprocess
import time


def snapshot(roots=None, known=None):
    """Inventory ancestry cheaply; fetch command identity only for candidate owners.

    Commands for unrelated processes can block while reading their argument pages.
    Both reads retain two-second deadlines. Final start-time/command equality is
    still required before any previously observed PID can be signalled.
    """
    roots = {os.getpid()} if roots is None else set(roots)
    known = {} if known is None else known
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,stat=,lstart='],
                            capture_output=True, text=True, check=True, timeout=2)
    inventory = {}
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) == 9:
            pid, parent, group = map(int, parts[:3])
            inventory[pid] = {'parent': parent, 'group': group,
                              'state': parts[3], 'start': tuple(parts[4:9])}
    candidates = {pid for pid in roots if pid in inventory}
    candidates.update(pid for pid, identity in known.items()
                      if pid in inventory and inventory[pid]['start'] == identity[:5])
    while True:
        children = {pid for pid, row in inventory.items() if row['parent'] in candidates}
        if children <= candidates:
            break
        candidates.update(children)
    if not candidates:
        return {}
    result = subprocess.run(['/bin/ps', '-p', ','.join(str(p) for p in sorted(candidates)),
                             '-o', 'pid=,lstart=,command='],
                            capture_output=True, text=True, timeout=2)
    if result.returncode not in (0, 1):
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    rows = {}
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 6)
        if len(parts) == 7:
            pid = int(parts[0]);start = tuple(parts[1:6])
            if pid in candidates and inventory[pid]['start'] == start:
                row = inventory[pid]
                rows[pid] = {'parent': row['parent'], 'group': row['group'],
                             'state': row['state'], 'identity': start + (parts[6],)}
    return rows


class OwnedTree:
    def __init__(self, pid, process=None):
        self.pid = pid
        self.process = process
        self.known = {}

    def observe(self):
        root_live = self.process is not None and self.process.poll() is None
        roots = {self.pid} if root_live or (self.process is None and self.pid not in self.known) else set()
        rows = snapshot(roots, self.known)
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
