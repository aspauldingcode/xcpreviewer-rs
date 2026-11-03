"""Assert the scoped native window/weak-load observation, not destructor acceptance."""
import argparse
import json
from pathlib import Path


def verify(root):
    events = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
    ui = json.loads((root / 'ui.json').read_text())
    assert all(a['time_ns'] <= b['time_ns'] for a, b in zip(events, events[1:]))
    assert not any(v['stage'] in ('failure', 'cleanup-unconfirmed', 'unload-error') for v in events)
    payloads = [v['message']['payload'] for v in events if v['stage'] == 'script']
    ready = next(v for v in payloads if v['event'] == 'hooks-ready')
    assert ready['uuid'] == 'afaf513ac1153755840e1d82b40e7d93'
    assert ready['runtime_uuid'] == '7669d858d33236c79c6c4564ffbea8d2'
    assert ready['weak_poll_main_queue'] and not ready['helper_module_loaded']
    seen = [v for v in payloads if v['event'] == 'editor-scene-observed']
    assert {v['id'] for v in seen} == {1, 2}
    assert all(v['main'] and v['expected_class'] and v['weak_alive_at_load'] for v in seen)
    calls = {}
    for v in payloads:
        if v['event'] == 'method-enter':
            assert v['call_id'] not in calls
            calls[v['call_id']] = v
        elif v['event'] == 'method-return':
            prior = calls.pop(v['call_id'])
            assert prior['scene_id'] == v['scene_id'] and prior['thread'] == v['thread']
    assert not calls
    paired = sum(v['event'] == 'method-return' for v in payloads)
    assert paired > 0
    assert not any(v['event'].startswith(('deinitializing-', 'deallocating-')) for v in payloads)
    snapshots = [v for v in payloads if v['event'] == 'snapshot']
    labels = ['baseline', 'unpinned', 'new-tab', 'after-close', 'restored']
    assert [v['label'] for v in snapshots] == labels
    for v in snapshots:
        assert v['main']
        assert {o['id'] for o in v['objects']} == ({1} if v['label'] in labels[:2] else {1, 2})
        assert all(o['weak_alive_at_load'] and not o['deinitializing_return_seen'] and not o['deallocating_return_seen'] for o in v['objects'])
        assert next(x['value'] for x in ui if x['kind'] == 'snapshot' and x['label'] == v['label']) == v
    snap_times = {v['message']['payload']['label']: v['time_ns'] for v in events if v['stage'] == 'script' and v['message']['payload']['event'] == 'snapshot'}
    assert snap_times['restored'] - snap_times['after-close'] >= 3_000_000_000
    inventory = {v['label']: v['windows'] for v in ui if v['kind'] == 'inventory'}
    original = inventory['before']; assert len(original) == 1
    original_id = original[0]['id']
    created = inventory['created']; assert len(created) == 2
    added = [v for v in created if v['id'] != original_id]; assert len(added) == 1
    assert all(v['pid'] == 45749 and v['title'] == 'PreviewLab — PreviewLab.swift' for group in inventory.values() for v in group)
    assert original_id in [v['id'] for v in created]
    after_close_index = next(i for i, v in enumerate(ui) if v['kind'] == 'snapshot' and v['label'] == 'after-close')
    settled = [v for v in ui[:after_close_index] if v['kind'] == 'inventory'][-1]
    assert settled['windows'] == original
    observations = {v['label']: v for v in ui if v['kind'] == 'observe'}
    assert all(v['ok'] and v['pid'] == 45749 for v in observations.values())
    assert [observations[k]['pin_identifier'] for k in ('before', 'unpinned', 'repinned', 'restored')] == ['pin.fill', 'pin', 'pin.fill', 'pin.fill']
    actions = [v for v in ui if v['kind'] == 'action']
    assert [v['args'].get('menu', v['args'].get('label')) for v in actions] == ['Pin Preview', 'Pin Preview', 'File>New>Window', 'Close window']
    assert all(v['data']['ok'] and v['data']['result']['ok'] for v in actions)
    close = observations['created']['close_frame']; frame = added[0]['frame']
    assert frame[0] <= close[0] < frame[0] + 50 and frame[1] <= close[1] < frame[1] + 50
    assert ui[-1] == {'kind': 'completed', 'original_window_preserved': True, 'created_window_closed': True}
    cleanup = next(v for v in payloads if v['event'] == 'cleanup-done')
    assert cleanup['weak_slots_destroyed'] == 2 and cleanup['main']
    assert [v['stage'] for v in events[-3:]] == ['script-unloaded', 'session-detached', 'session-ended-no-target-termination']
    post = json.loads((root / 'postflight.json').read_text())
    assert post['controller_available'] and post['executable'] == '/Applications/Xcode.app/Contents/MacOS/Xcode'
    assert post['source_sha256'] == '128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef'
    assert post['project_sha256'] == '1ee671965dcfb221233970e970130946a1971a0b0d30625601e93440a60bcf45'
    return {'paired_setters': paired, 'sampled_receivers_after_window_close': 2, 'target_destruction_verified': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('directory', type=Path)
    print(json.dumps(verify(p.parse_args().directory), indent=2))
