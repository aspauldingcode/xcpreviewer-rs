"""Explicit, independently testable macOS public libproc snapshot backend.

Execution is in a separate owned helper with a two-second deadline. Executable
path plus microsecond birth time replaces ps command/start text; argument changes
are not identities. Callers must retain full equality before signalling. Backend
selection must remain fixed throughout an OwnedTree's lifetime.
"""
import json
import os
import pathlib
import subprocess
import sys
from reloop.core import ROOT, digest


def build(folder):
    if sys.platform != 'darwin':
        raise RuntimeError('Public libproc helper requires macOS')
    folder = pathlib.Path(folder); folder.mkdir(parents=True, exist_ok=True)
    source = ROOT/'tools/re/native/OwnedProcessSnapshot.c'
    binary = folder/'owned-process-snapshot'
    argv = ['/usr/bin/clang', '-std=c11', '-Wall', '-Wextra', '-Werror', str(source), '-lproc', '-o', str(binary)]
    with (folder/'compile.stdout').open('wb') as out, (folder/'compile.stderr').open('wb') as err:
        subprocess.run(argv, stdout=out, stderr=err, check=True, timeout=10)
    return Observer(binary), {'source_sha256':digest(source),'binary_sha256':digest(binary),
                              'compiler_sha256':digest('/usr/bin/clang'),'argv':argv}


class Observer:
    def __init__(self, binary):
        self.binary = str(pathlib.Path(binary).absolute())

    def snapshot(self, roots=None, known=None):
        roots = {os.getpid()} if roots is None else set(roots)
        known = {} if known is None else known
        if any(type(pid) is not int or not 0<pid<=2147483647 for pid in roots):raise ValueError('Invalid owned root')
        args = [str(pid) for pid in sorted(roots)]
        for pid, identity in sorted(known.items()):
            if len(identity)==3 and all(type(v) is int and v>=0 for v in identity[:2]):
                args.append('%d:%d:%d' % (pid, *identity[:2]))
        result = subprocess.run([self.binary,*args],capture_output=True,check=True,timeout=2)
        data = json.loads(result.stdout)
        if not isinstance(data,list): raise ValueError('Invalid libproc snapshot')
        rows = {}
        for row in data:
            pid = row['pid']; identity = row['identity']
            if (type(pid) is not int or pid<=0 or pid in rows or len(identity)!=3
                    or any(type(v) is not int or v<0 for v in identity[:2])
                    or not isinstance(identity[2],str) or not identity[2].startswith('/')
                    or any(type(row[k]) is not int or row[k]<0 for k in ('parent','group'))
                    or row['state'] not in ('L','Z')):
                raise ValueError('Invalid libproc process identity')
            # The C JSON string escapes raw path bytes as Latin-1 codepoints.
            # Decode through filesystem semantics, including non-UTF8 bytes.
            identity[2]=os.fsdecode(identity[2].encode('latin1'))
            row['identity']=tuple(identity); rows[pid]=row
        for pid in roots-set(rows):
            try:os.kill(pid,0)
            except ProcessLookupError:continue
            raise OSError('Cannot observe a live owned root')
        # The helper emits only candidate ancestry. Retired known PIDs are still
        # checked by OwnedTree for complete birth-time AND executable equality.
        return rows
