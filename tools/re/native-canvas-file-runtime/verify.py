"""Verify recorded native file-event paths; no native rerun or exact boundary claim."""
import argparse
import json
from pathlib import Path


def verify(path):
    rows = [json.loads(x) for x in (path/'events.jsonl').read_text().splitlines()]
    assert not any(r.get('status') == 'failed' or r.get('stage') == 'early-file-write-failed' for r in rows)
    assert not any(r.get('message', {}).get('type') == 'error' for r in rows)
    assert any(r.get('status') == 'all-file-actions-complete' for r in rows)
    assert rows[-1].get('status') == 'detached-no-target-termination' and rows[-1]['source_restored']
    callbacks = [(r, r['message']['payload']) for r in rows if r.get('message', {}).get('type') == 'send']
    assert all(r['phase'] == p['agent_phase'] for r, p in callbacks)
    assert not any(p['event'].startswith('modified-') for r, p in callbacks if r['phase'] == 'baseline')
    def unique(items):
        assert len(items) == 1, len(items)
        return items[0]
    stamp = unique([r for r, p in callbacks if p['event'] == 'build-timestamp-written'])
    early_write = unique([r for r in rows if r.get('stage') == 'early-file-write'])
    late_write = unique([r for r in rows if r.get('stage') == 'late-file-write'])
    completed = unique([r for r in rows if r.get('stage') == 'build-result'])
    assert stamp['time_ns'] < early_write['time_ns'] < completed['time_ns'] < late_write['time_ns']
    receipt = json.loads((path/'early-result.json').read_text())
    assert receipt['code'] == 0 and not receipt['timeout'] and receipt['stdout'].strip() == 'true, succeeded'
    results = {}
    for phase, branch, write in [('early', 'modified-time-suppressed-cleanup', early_write),
                                  ('late', 'modified-time-pass', late_write),
                                  ('restore', 'modified-time-pass', unique([r for r in rows if r.get('stage') == 'source-restored']))]:
        matches = [(r, p) for r, p in callbacks if r['phase'] == phase and p['event'] == 'modified-time-check']
        check, payload = unique(matches)
        invocation = payload['invocation']
        group = [(r, p) for r, p in callbacks if p.get('invocation') == invocation]
        names = [p['event'] for r, p in group]
        expected = ['workspace-event-handler', 'modified-timestamp-presence', 'modified-time-check', branch]
        assert [n for n in names if n in expected] == expected
        assert names[-1] == 'workspace-event-handler-return'
        assert all(p['thread'] == payload['thread'] for r, p in group)
        assert write['time_ns'] < check['time_ns']
        assert all(r['phase'] == phase for r, p in group)
        if phase == 'early':
            assert 'modified-time-pass' not in names and 'modified-file-filter' not in names
        else:
            assert names.index('modified-file-filter') > names.index(branch)
            assert 'modified-time-suppressed-cleanup' not in names
        predicates = {p['event']: p['value'] for r, p in group if p['event'].endswith('-result')}
        if 'is-open-thunkable-result' in (path/'agent.js').read_text() and phase != 'early':
            assert predicates == {'is-open-thunkable-result': 1, 'should-update-file-result': 0}
        results[phase] = dict(invocation=invocation, path=branch, filter_entered='modified-file-filter' in names,
                              predicates=predicates, scene_update_entry_observed='modified-scene-update' in names,
                              host_reception_seconds_since_timestamp=(check['time_ns']-stamp['time_ns'])/1e9)
    return dict(classification='native basic-block paths during real file modifications', phases=results,
                exact_two_second_boundary_verified=False, full_refresh_or_rendering_verified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    print(json.dumps(verify(parser.parse_args().directory), indent=2))
