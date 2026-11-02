"""Assert captured executions; this does not rerun Xcode or prove full refresh parity."""
import argparse
import json
from pathlib import Path


def verify(directory):
    rows = [json.loads(line) for line in (directory / 'events.jsonl').read_text().splitlines()]
    assert not any(r.get('status') == 'failed' for r in rows), 'driver failure'
    assert not any(r.get('message', {}).get('type') == 'error' for r in rows), 'agent failure'
    assert any(r.get('status') == 'all-build-actions-complete' for r in rows), 'missing completion'
    assert rows[-1].get('status') == 'detached-no-target-termination', 'missing detach receipt'
    assert rows[-1]['source_restored'], 'source not restored'
    results = {}
    for phase, expected_status, result in [('success', 'succeeded', 1), ('failure', 'failed', 2), ('recovery', 'succeeded', 1)]:
        group = [r for r in rows if r['phase'] == phase]
        request = next(i for i, r in enumerate(group) if r.get('stage') == 'build-request')
        finished = next(i for i, r in enumerate(group) if r.get('stage') == 'build-result')
        window = group[request + 1:finished]
        callbacks = [(i, r['message']['payload']) for i, r in enumerate(window)
                     if r.get('message', {}).get('type') == 'send']
        def one(name):
            found = [(i, p) for i, p in callbacks if p['event'] == name]
            assert len(found) == 1, (phase, name, len(found))
            return found[0]
        start, start_payload = one('build-start-listener')
        flag, flag_payload = one('isPreviewsBuild')
        stop, stop_payload = one('build-stop-listener')
        read, read_payload = one('build-result-read')
        assert start < flag < stop < read, (phase, 'callback order')
        assert flag_payload['value'] == 0 and read_payload['value'] == result
        thread = start_payload['thread']
        assert all(p['thread'] == thread for p in [flag_payload, stop_payload, read_payload])
        # An entry alone establishes execution, not its payload or downstream effects.
        handlers = [i for i, p in callbacks if p['event'] == 'workspace-event-handler']
        assert any(flag < i < stop for i in handlers), (phase, 'start handler absent')
        assert any(i > read for i in handlers), (phase, 'stop handler absent')
        marked = [p for _, p in callbacks if 'agent_phase' in p]
        if marked:
            assert len(marked) == len(callbacks) and all(p['agent_phase'] == phase for p in marked)
        receipt = json.loads((directory / (phase + '-result.json')).read_text())
        assert receipt['code'] == 0 and not receipt['timeout']
        assert receipt['stdout'].strip() == 'true, ' + expected_status
        assert group[finished]['stdout'] == receipt['stdout']
        results[phase] = dict(status=expected_status, result_read=result, is_previews_build=False,
                              thread=thread, workspace_handler_entries=len(handlers),
                              agent_phase_marked=bool(marked))
    return dict(classification='native listener execution during actual Xcode builds', phases=results,
                source_restored=True, full_refresh_or_product_acceptance=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.directory), indent=2))
