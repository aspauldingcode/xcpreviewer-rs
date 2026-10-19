def _require(condition):
    if not condition:
        raise AssertionError('GPU lifecycle evidence rejected')

import base64, hashlib, json, re
from pathlib import Path

def verify(folder):
    e = Path(folder)
    m = json.loads((e / 'manifest.json').read_text())
    _require(set(m['files']) == {str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name != 'manifest.json'})
    for (n, x) in m['files'].items():
        _require(not Path(n).is_absolute() and '..' not in Path(n).parts)
        p = e / n
        _require(not p.is_symlink())
        b = p.read_bytes()
        _require(len(b) == x['bytes'] and hashlib.sha256(b).hexdigest() == x['sha256'])
    _require(json.loads((e / 'prediction.json').read_text())['parent_manifest_sha256'] == 'a2fc1388b339af82b3c0d52f5ac0b4f27b350d696ca515c15730a7d484792a89')
    rea = json.loads((e / 'rea.json').read_text())
    _require(rea['closed'] is True and rea['identity']['package']['version'] == '6.2.0')
    _require(json.loads((e / 'compile.json').read_text()) == {'wait': 0, 'stdout': '', 'stderr': ''})
    env = json.loads((e / 'environment.json').read_text())
    _require(env['machine'].strip() == 'arm64' and '26.6' in env['xcode'] and ('25F80' in env['sw_vers']))
    _require(rea['inspection']['subject']['digest']['sha256'] == env['helper_sha256'] == rea['open']['result']['sha256'])

    def integer(x, v):
        _require(type(x) is int and x == v)
    expected = bytearray([92] * 16384)
    for y in range(6):
        expected[y * 256:y * 256 + 44] = bytes([119] * 44)
    total = 0
    parents = set()
    peers = set()
    jobs = set()
    for (mode, value, exit) in [('before', 3, 47), ('after', 7, 48)]:
        root = e / mode
        _require(json.loads((root / 'environment.json').read_text()) == env)
        for i in range(2):
            w = json.loads((root / f'wait-{i}.json').read_text())
            _require(w['mode'] == mode and w['helper_sha256'] == env['helper_sha256'] and ('owned_parent_deadline_kill' not in w))
            for k in ['bootstrap_wait', 'parent_wait', 'print_wait', 'bootout_wait']:
                integer(w[k], 0)
            integer(w['last_exit_code'], exit)
            integer(w['after_cleanup_print_wait'], 113)
            for k in ['bootstrap_stderr', 'parent_stderr', 'bootout_stderr', 'peer_stderr']:
                _require(w[k] == '')
            _require(w['peer_running_after_finish'] is False and w['program_matches'] is True and (w['plist_removed'] is True))
            _require(w['domain'] == 'gui/503' and re.fullmatch('org.xcpreviewer.owned-event-[0-9a-f]{32}', w['job']))
            _require(w['job'] not in jobs)
            jobs.add(w['job'])
            d = json.loads((root / f'result-{i}.json').read_text())
            _require(d['device'] == 'Apple M1' and d['unified_memory'] is True and (d['pending_timeout'] is True) and (d['reply'] is None) and (d['rpc_error'] == 'NSCocoaErrorDomain'))
            for (k, v) in [('pending_callbacks', 0), ('pending_value', 3), ('reply_wait', 0), ('value_after_rpc', value), ('completion_wait', 0), ('completion_status', 4), ('callbacks', 1), ('rpc_error_code', 4097), ('rpc_error_count', 1), ('peer_pid', 0), ('rpc_pending_callbacks', 0)]:
                integer(d[k], v)
            if mode == 'before':
                _require(type(d['rpc_pending_wait']) is int and d['rpc_pending_wait'] > 0)
            else:
                integer(d['rpc_pending_wait'], 0)
            pid = d['pid']
            _require(type(pid) is int and pid > 0)
            integer(w['parent_pid'], pid)
            _require(pid not in parents)
            parents.add(pid)
            peer = json.loads(w['peer_stdout'])
            peerpid = peer['pid']
            _require(type(peerpid) is int and peerpid > 0 and (peerpid != pid) and (peerpid not in peers))
            peers.add(peerpid)
            for (k, v) in [('accepted_parent', pid), ('exit', exit), ('imported_value', value), ('wrong_value', 99)]:
                integer(peer[k], v)
            for (k, v) in [('before', bytes([92] * 16384)), ('after', expected)]:
                b = base64.b64decode(d[k], validate=True)
                _require(b == v)
                total += len(b)
    _require(total == 131072)
    return {'complete_bytes': total, 'parent_waits': 4, 'owned_services_removed': 4, 'expected_peer_exits': [47, 47, 48, 48]}
