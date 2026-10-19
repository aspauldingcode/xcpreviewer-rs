"""Fail-closed frozen full-allocation failure/timeout evidence reader."""
import math
def _require(condition):
    if not condition:raise AssertionError('Surface failure evidence rejected')
def _integer(value):
    _require(type(value) is int and value>=0)
def _pid(value):
    _require(type(value) is int and 1<value<=2147483647)
def _json(raw):
    def pairs(items):
        d={}
        for k,v in items:
            _require(k not in d)
            d[k]=v
        return d
    def constant(v):raise AssertionError('Nonfinite JSON rejected')
    v=json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
    def finite(x):
        if type(x) is float:_require(math.isfinite(x))
        elif type(x) is list:
            for y in x:finite(y)
        elif type(x) is dict:
            for y in x.values():finite(y)
    finite(v)
    return v
import hashlib, json
from pathlib import Path

def verify(folder):
    e = Path(folder)
    m = _json((e / 'manifest.json').read_text())
    _require(set(m['files']) == {str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name != 'manifest.json'})
    for (n, x) in m['files'].items():
        _integer(x['bytes'])
        _require(not Path(n).is_absolute() and '..' not in Path(n).parts)
        p = e / n
        _require(not p.is_symlink())
        b = p.read_bytes()
        _require(len(b) == x['bytes'] and hashlib.sha256(b).hexdigest() == x['sha256'])
    compile = _json((e / 'compile.json').read_text())
    _integer(compile['code'])
    _require(compile['code'] == 0 and compile['timeout'] is False)
    wait = _json((e / 'wait.json').read_text())
    _integer(wait['code'])
    _require(wait['code'] == 0 and wait['timeout'] is False and (wait['stderr'] == ''))
    rows = [_json(x) for x in wait['stdout'].splitlines()]
    _require(len(rows) == 2)
    expected = bytearray([165]) * 16384
    for y in range(9):
        for x in range(17):
            for c in range(4):
                expected[y * 128 + x * 4 + c] = 255 if c == 3 else 49 + x * 17 + y * 31 + c * 53 & 255
    total = 0
    parents = []
    children = []
    for (row, phase, code, exit_, signal, cleanup) in zip(rows, ['after-import', 'before-ack'], [0, 268451843], [42, -1], [0, 9], ['explicit', 'process-teardown']):
        for (k, v) in {'phase': phase, 'width': 17, 'height': 9, 'seed': 49, 'stride': 128, 'allocation_bytes': 16384, 'mach_error': code, 'peer_exit': exit_, 'peer_signal': signal, 'receiver_cleanup': cleanup, 'local_resource_refs_retained': 1, 'completion_accepted': False, 'late_ack_received': False, 'audit_peer_verified': True, 'failure_observed': True, 'local_resource_name_removed': True, 'peer_endpoint_name_removed': True, 'rendezvous_removed': True}.items():
            _require(row[k] == v and type(row[k]) is type(v))
        _pid(row['sender_pid'])
        _pid(row['receiver_pid'])
        parents.append(row['sender_pid'])
        children.append(row['receiver_pid'])
        _require(row['sender_pid'] > 1 and row['receiver_pid'] > 1 and (row['sender_pid'] != row['receiver_pid']))
        for name in ['imported.bin', 'retained.bin']:
            raw = (e / phase / name).read_bytes()
            _require(raw == expected)
            total += len(raw)
    _require(parents[0] == parents[1] and children[0] != children[1] and (total == 65536))
    env = _json((e / 'environment.json').read_text())
    rea = _json((e / 'rea.json').read_text())
    _require(rea['open']['result']['sha256'] == rea['identity']['result']['sha256'] == env['helper_sha256'] == '5e6ec2b74e80c0f1e8684c3c5c8fddf1745cae9f92512b5bb58962ecdf1bab62')
    _require(rea['identity']['result']['architecture'] == 'arm64' and rea['closed']['result'] is None)
    prior = _json((e / 'prior-verification.json').read_text())
    _require(len(prior) == 3 and all((x['valid'] is True and x['external_anchor_matches'] is True for x in prior)))
    return {'full_allocation_bytes': total, 'padding_bytes': 2160, 'unused_tail_bytes': 60928, 'physical_reclamation': False}
