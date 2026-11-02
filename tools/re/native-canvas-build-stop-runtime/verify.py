"""Assert native build-stop false-preference control; no true-gate or rendering claim."""
import argparse
import json
from pathlib import Path


def verify(directory):
    rows = [json.loads(x) for x in (directory/'events.jsonl').read_text().splitlines()]
    assert not any(r.get('status') == 'failed' or r.get('message', {}).get('type') == 'error' for r in rows)
    assert any(r.get('status') == 'all-build-actions-complete' for r in rows)
    assert rows[-1].get('status') == 'detached-no-target-termination' and rows[-1]['source_restored']
    callbacks = [(r, r['message']['payload']) for r in rows if r.get('message', {}).get('type') == 'send']
    assert all(r['phase'] == p['agent_phase'] for r, p in callbacks)
    def one(items, label):
        assert len(items) == 1, (label, 'expected one, observed', len(items))
        return items[0]
    results = {}
    for phase, status, result, flag in [('success', 'succeeded', 1, 1), ('failure', 'failed', 2, 0), ('recovery', 'succeeded', 1, 1)]:
        phase_rows = [r for r in rows if r['phase'] == phase]
        request = one([r for r in phase_rows if r.get('stage') == 'build-request'], phase)
        complete = one([r for r in phase_rows if r.get('stage') == 'build-result'], phase)
        window = [(r, p) for r, p in callbacks if request['time_ns'] < r['time_ns'] < complete['time_ns']]
        start, _ = one([(r, p) for r, p in window if p['event'] == 'build-start-listener'], 'start')
        stop, _ = one([(r, p) for r, p in window if p['event'] == 'build-stop-listener'], 'stop')
        read, read_payload = one([(r, p) for r, p in window if p['event'] == 'build-result-read'], 'result')
        gate, payload = one([(r, p) for r, p in window if p['event'] == 'build-stop-preference-inputs'], 'preference inputs')
        assert start['time_ns'] < stop['time_ns'] < read['time_ns'] < gate['time_ns']
        assert read_payload['value'] == result
        assert payload['preference'] == 0 and payload['success_payload'] == flag
        group = [(r, p) for r, p in callbacks if p.get('invocation') == payload['invocation']]
        assert [p['event'] for r, p in group] == ['workspace-event-handler', 'build-stop-preference-inputs',
                                                'shared-gate-return-path', 'workspace-event-handler-return']
        assert all(p['thread'] == payload['thread'] and r['phase'] == phase for r, p in group)
        receipt = json.loads((directory/(phase+'-result.json')).read_text())
        assert receipt['code'] == 0 and not receipt['timeout'] and receipt['stdout'].strip() == 'true, '+status
        assert complete['stdout'] == receipt['stdout']
        results[phase] = dict(status=status, result_read=result, loaded_preference=False, success_payload=bool(flag),
                              invocation=payload['invocation'], returned_before_scene_state_and_refresh=True)
    return dict(classification='native build-stop loaded-false preference path', phases=results,
                true_preference_branch_verified=False, rendering_or_full_product_verified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    print(json.dumps(verify(parser.parse_args().directory), indent=2))
