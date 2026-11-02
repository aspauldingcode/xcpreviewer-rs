"""Assert actual positive modified-file selection traces, not rendered completion."""
import argparse
import json
from pathlib import Path


def verify(directory):
    rows = [json.loads(x) for x in (directory/'events.jsonl').read_text().splitlines()]
    assert not any(r.get('status') == 'failed' or r.get('message', {}).get('type') == 'error' for r in rows)
    assert any(r.get('status') == 'all-passing-file-actions-complete' for r in rows)
    assert any(r.get('stage') == 'fixture-removed' for r in rows)
    last = rows[-1]
    assert last.get('status') == 'detached-no-target-termination'
    assert all(last[k] for k in ['source_restored', 'project_restored', 'dependency_absent'])
    callbacks = [(r, r['message']['payload']) for r in rows if r.get('message', {}).get('type') == 'send']
    assert all(r['phase'] == p['agent_phase'] for r, p in callbacks)
    assert not any(p['event'].startswith('modified-') for r, p in callbacks if r['phase'] == 'baseline')
    receipt = json.loads((directory/'build-result.json').read_text())
    assert receipt['code'] == 0 and not receipt['timeout']
    assert receipt['stdout'].strip() == 'true, succeeded, true', 'build success and dependency-name build-log marker required'
    def one(items):
        assert len(items) == 1, len(items)
        return items[0]
    completed = one([r for r in rows if r.get('stage') == 'build-result'])
    results = {}
    for phase, write_stage in [('change', 'dependency-write'), ('restore-value', 'dependency-restored-value')]:
        write = one([r for r in rows if r.get('stage') == write_stage])
        check, payload = one([(r, p) for r, p in callbacks if r['phase'] == phase and p['event'] == 'modified-time-check'])
        assert completed['time_ns'] < write['time_ns'] < check['time_ns']
        group = [(r, p) for r, p in callbacks if p.get('invocation') == payload['invocation']]
        names = [p['event'] for r, p in group]
        expected = ['modified-timestamp-presence', 'modified-time-check', 'modified-time-pass', 'modified-file-filter',
                    'is-open-thunkable-result', 'should-update-file-result', 'environment-coalescer-set-needs-update',
                    'workspace-scene-set-needs-update', 'workspace-scene-set-needs-update-return']
        assert [n for n in names if n in expected] == expected
        assert names[0] == 'workspace-event-handler' and names[-1] == 'workspace-event-handler-return'
        assert 'modified-time-suppressed-cleanup' not in names
        assert all(p['thread'] == payload['thread'] and r['phase'] == phase for r, p in group)
        values = {p['event']: p['value'] for r, p in group if 'value' in p}
        assert values == {'is-open-thunkable-result': 0, 'should-update-file-result': 1}
        callers = {p['event']: p['caller_offset'] for r, p in group if 'caller_offset' in p}
        if 'caller_offset' in (directory/'agent.js').read_text():
            assert callers == {'environment-coalescer-set-needs-update': '0x249c84',
                               'workspace-scene-set-needs-update': '0x24a2ec'}, callers
        results[phase] = dict(invocation=payload['invocation'], is_open_and_thunkable=False,
                              should_update_file=True, coalescer_entry=True, scene_update_entry_and_return=True,
                              caller_offsets=callers)
    return dict(classification='native passing modified-file route and scene-update method execution', phases=results,
                fixture_removed=True, rendered_completion_verified=False, full_product_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    print(json.dumps(verify(parser.parse_args().directory), indent=2))
