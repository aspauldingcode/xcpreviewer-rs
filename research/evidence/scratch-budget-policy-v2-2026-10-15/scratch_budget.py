"""Research-only accounting proposal; not wired into the native controller.

Retained files always count by logical size. Only three explicitly named CAS
scratch files may count by allocation, with independent aggregate caps. This
does not provide a race-free filesystem sandbox or native build acceptance.
"""
import os
from pathlib import Path
import stat
import tempfile
import time

GIB = 1024 ** 3
CAS = {
    'DerivedData/CompilationCache.noindex/generic/v1.1/v8.data': 16 * GIB,
    'DerivedData/CompilationCache.noindex/generic/v1.1/v8.index': 8 * GIB,
    'DerivedData/CompilationCache.noindex/generic/v1.1/v3.actions': GIB,
}


def new_root(parent):
    """Create a fresh private run directory; callers retain creation provenance."""
    root = Path(tempfile.mkdtemp(prefix='owned-scratch-', dir=parent))
    row = root.lstat()
    return root, (row.st_dev, row.st_ino)


def measure(root, identity=None, deadline=None, max_entries=100000):
    root = Path(root)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise ValueError('Owned real directory required')
    if identity is not None and ((info.st_dev, info.st_ino) != identity
                                 or stat.S_IMODE(info.st_mode) & 0o077):
        raise ValueError('Private run-root identity changed')
    if type(max_entries) is not int or max_entries < 0 or max_entries > 100000:
        raise ValueError('Invalid traversal entry bound')
    def check_bound():
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError('Accounting traversal deadline')
        if result['files'] + result['directories'] > max_entries:
            raise ValueError('Traversal entry budget exceeded')
    result = dict(retained_logical=0, scratch_logical=0, allocated=0, files=0, directories=0)
    def traversal_error(error):
        raise error
    for folder, dirs, files in os.walk(root, followlinks=False, onerror=traversal_error):
        check_bound()
        for name in dirs + files:
            check_bound()
            path = Path(folder) / name
            row = path.lstat()
            if row.st_uid != os.getuid() or stat.S_ISLNK(row.st_mode):
                raise ValueError('Unowned or symlink entry')
            if stat.S_ISDIR(row.st_mode):
                result['directories'] += 1
                check_bound()
                continue
            if not stat.S_ISREG(row.st_mode) or row.st_nlink != 1:
                raise ValueError('Only private regular files admitted')
            relative = path.relative_to(root).as_posix()
            allocated = row.st_blocks * 512
            maximum = CAS.get(relative)
            if maximum is not None and row.st_size > maximum:
                raise ValueError('CAS logical extent exceeds declared shape')
            if maximum is not None and row.st_size == maximum and allocated < row.st_size:
                result['scratch_logical'] += row.st_size
            else:
                result['retained_logical'] += row.st_size
            result['allocated'] += allocated
            result['files'] += 1
            check_bound()
    final = root.lstat()
    if (final.st_dev, final.st_ino) != (info.st_dev, info.st_ino):
        raise ValueError('Run root replaced during measurement')
    check_bound()
    return result


def admit(values):
    keys = ('retained_logical', 'scratch_logical', 'allocated', 'files', 'directories')
    if any(type(values.get(key)) is not int or values[key] < 0 for key in keys):
        return False
    return (values['retained_logical'] <= 512 * 1024 ** 2
            and values['allocated'] <= 512 * 1024 ** 2
            and values['scratch_logical'] <= 25 * GIB
            and values['files'] + values['directories'] <= 100000)
