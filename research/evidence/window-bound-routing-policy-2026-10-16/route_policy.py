"""Research-only admission model. No UI actions or platform calls are performed."""
from dataclasses import dataclass
import posixpath

class Denied(ValueError):
    pass

@dataclass(frozen=True)
class Window:
    pid: int
    birth_seconds: int
    birth_microseconds: int
    window_id: int
    document: str

def validate(window, owned_root):
    if type(window) is not Window:
        raise Denied('No explicit window binding')
    if any(type(v) is not int for v in [window.pid,window.birth_seconds,window.birth_microseconds,window.window_id]):
        raise Denied('Invalid process/window identity types')
    if window.pid<=0 or window.window_id<=0 or window.birth_seconds<0 or not 0<=window.birth_microseconds<1000000:
        raise Denied('Invalid process/window identity')
    for path in [owned_root,window.document]:
        if type(path) is not str or not 1<len(path)<=4096 or '\0' in path or not path.startswith('/') or path.startswith('//') or posixpath.normpath(path)!=path:
            raise Denied('Noncanonical lexical path')
    if not window.document.startswith(owned_root+'/'):
        raise Denied('Document outside declared owned root')

def capabilities(values):
    if type(values) not in (tuple,list) or len(values)>64:
        raise Denied('Capability collection required')
    if any(type(v) is not str or not 0<len(v)<=64 or '\0' in v for v in values):
        raise Denied('Malformed capability')
    return values

def decide(op,captured,current,owned_root,ax_actions,advertised,frontmost_pid=None,hit_window_id=None,element_window=None):
    for window in [captured,current,element_window]:
        validate(window,owned_root)
    if captured!=current or element_window!=current:
        raise Denied('Captured or element ancestor process/window/document identity changed')
    capabilities(ax_actions);capabilities(advertised)
    if op=='press':
        if 'AXPress' not in ax_actions:
            raise Denied('Requested AXPress unavailable; no implicit pointer fallback')
        return 'PRESS'
    if op=='click':
        if type(frontmost_pid) is not int or type(hit_window_id) is not int:
            raise Denied('Exact integer foreground and hit-window identities required')
        if 'CLICK' not in advertised or frontmost_pid!=current.pid or hit_window_id!=current.window_id:
            raise Denied('Pointer capability, foreground or hit-window binding missing')
        return 'CLICK'
    raise Denied('Unsupported operation')
