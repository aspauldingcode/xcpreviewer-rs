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
    _require(json.loads((e / 'prediction.json').read_text())['parent_manifest_sha256'] == '103b36861e57935e078de43f8c86473021f00bc5400b6ec7eb26f72ec125ca06')
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
    for (mode, value) in [('retain', 7), ('drop', 3)]:
        root = e / mode
        _require(json.loads((root / 'environment.json').read_text()) == env)
        drop = mode == 'drop'
        for i in range(2):
            w = json.loads((root / f'wait-{i}.json').read_text())
            _require(w['mode'] == mode and w['helper_sha256'] == env['helper_sha256'] and ('owned_parent_deadline_kill' not in w))
            for k in ['bootstrap_wait', 'parent_wait', 'print_wait', 'bootout_wait', 'last_exit_code']:
                integer(w[k], 0)
            integer(w['after_cleanup_print_wait'], 113)
            for k in ['bootstrap_stderr', 'parent_stderr', 'bootout_stderr', 'peer_stdout', 'peer_stderr']:
                _require(w[k] == '')
            _require(w['peer_running_after_finish'] is False and w['program_matches'] is True and (w['plist_removed'] is True))
            _require(w['domain'] == 'gui/503' and re.fullmatch('org.xcpreviewer.owned-event-[0-9a-f]{32}', w['job']))
            _require(w['job'] not in jobs)
            jobs.add(w['job'])
            d = json.loads((root / f'result-{i}.json').read_text())
            _require(d['device'] == 'Apple M1' and d['unified_memory'] is True and (d['pending_timeout'] is True) and (d['finish_reply'] is True) and (d['original_owners_cleared'] is True) and (d['drop'] is drop))
            _require(d['rpc_error'] is None and d['second_error'] is None)
            for (k, v) in [('pending_callbacks', 0), ('pending_value', 3), ('reply_wait', 0), ('value_after_rpc', 3), ('after_disconnect', 3), ('disconnected_callbacks', 0), ('second_wait', 0), ('after_second', value), ('completion_wait', 0), ('completion_status', 4), ('callbacks', 1), ('finish_wait', 0), ('rpc_pending_callbacks', 0)]:
                integer(d[k], v)
            _require(type(d['disconnected_wait']) is int and d['disconnected_wait'] > 0)
            if drop:
                _require(type(d['rpc_pending_wait']) is int and d['rpc_pending_wait'] > 0)
            else:
                integer(d['rpc_pending_wait'], 0)
            pid = d['pid']
            peer = d['peer_pid']
            _require(type(pid) is int and pid > 0 and (type(peer) is int) and (peer > 0) and (peer != pid))
            integer(w['parent_pid'], pid)
            integer(d['second_pid'], peer)
            _require(pid not in parents and peer not in peers)
            parents.add(pid)
            peers.add(peer)
            first = d['reply']
            second = d['second_reply']
            _require(first['present'] is True and second['before_present'] is True and (second['after_present'] is (not drop)))
            for row in [first, second]:
                integer(row['pid'], peer)
                integer(row['accepted_parent'], pid)
            integer(first['value'], 3)
            token = first['token']
            _require(type(token) is int and token > 0)
            integer(second['before_token'], token)
            integer(second['after_token'], 0 if drop else token)
            if drop:
                _require(second['value'] is None)
            else:
                integer(second['value'], 7)
            for (k, v) in [('before', bytes([92] * 16384)), ('after', expected)]:
                b = base64.b64decode(d[k], validate=True)
                _require(b == v)
                total += len(b)
    _require(total == 131072)
    return {'complete_bytes': total, 'parent_waits': 4, 'owned_services_removed': 4}
