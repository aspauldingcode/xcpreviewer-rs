"""Research-only release admission from an actual native Xcode window inventory."""
import re
import os
import posixpath

def may_release(message, owned_root, required_user_workspaces):
    if not isinstance(message,str) or not message.strip():
        return False
    if not isinstance(owned_root,str) or not owned_root.startswith('/'):
        return False
    def canonical(p):
        return isinstance(p,str) and p.startswith('/') and not p.startswith('//') and posixpath.normpath(p)==p and '\x00' not in p
    if not canonical(owned_root) or type(required_user_workspaces) not in (list,tuple) or not required_user_workspaces or not all(canonical(p) for p in required_user_workspaces):
        return False
    paths=[];tabs=set()
    if message.strip()!='No workspace windows found':
        for line in message.strip().splitlines():
            row=re.fullmatch(r'\* tabIdentifier: (windowtab[0-9]+), workspacePath: (/[^\r\n]+)',line)
            if not row or row[1] in tabs or not canonical(row[2]):
                return False
            tabs.add(row[1]);paths.append(row[2])
    resolved_root=os.path.realpath(owned_root).rstrip('/')
    if any(os.path.realpath(p)==resolved_root or os.path.realpath(p).startswith(resolved_root+'/') for p in paths):
        return False
    return set(required_user_workspaces).issubset(paths)
