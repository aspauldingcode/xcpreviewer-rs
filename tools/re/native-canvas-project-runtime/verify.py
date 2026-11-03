"""Read scoped actual project-close observations; never assert target destruction."""
import argparse
import json
from pathlib import Path


def verify(root):
    rows=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    assert all(a['time_ns']<=b['time_ns'] for a,b in zip(rows,rows[1:]))
    assert not any(v['stage'] in ['failure','cleanup-unconfirmed','unload-error'] for v in rows)
    events=[v['message']['payload'] for v in rows if v['stage']=='script']
    ready=next(v for v in events if v['event']=='hooks-ready')
    assert ready['uuid']=='afaf513ac1153755840e1d82b40e7d93'
    assert ready['runtime_uuid']=='7669d858d33236c79c6c4564ffbea8d2'
    assert ready['weak_poll_main_queue'] and not ready['helper_module_loaded']
    assert next(v for v in rows if v['stage']=='owned-controls-passed')['count']==3
    observed=[v for v in events if v['event']=='editor-scene-observed']
    assert [v['id'] for v in observed]==[1,2]
    assert all(v['main'] and v['expected_class'] and v['weak_alive_at_load'] for v in observed)
    active={};paired=0
    for v in events:
        if v['event']=='method-enter':
            assert v['call_id'] not in active and v['scene_id'] in [1,2]
            active[v['call_id']]=v
        elif v['event']=='method-return':
            enter=active.pop(v['call_id']);assert enter['scene_id']==v['scene_id'] and enter['thread']==v['thread'];paired+=1
    assert not active and paired>0
    assert not any(v['event'].startswith(('deinitializing-','deallocating-')) for v in events)
    snaps=[v for v in events if v['event']=='snapshot']
    assert [v['label'] for v in snaps]==['baseline','unpinned','new-tab','after-close','restored']
    for v in snaps:
        assert v['main'] and 'temporary strong reference released on main' in v['weak_read_scope']
        assert [o['id'] for o in v['objects']]==([1,2] if v['label']=='restored' else [1])
        assert all(o['weak_alive_at_load'] and not o['deinitializing_return_seen'] and not o['deallocating_return_seen'] for o in v['objects'])
    ui=json.loads((root/'ui.json').read_text());obs={v['label']:v['data'] for v in ui if v['kind']=='observe'}
    assert obs['before']['pid']==45749 and obs['before']['window']=='PreviewLab — PreviewLab.swift'
    assert obs['before']['pin_identifier']=='pin.fill' and obs['unpinned']['pin_identifier']=='pin'
    assert obs['after-project-close']['ok'] is False and obs['after-project-close']['error']=='Xcode has no accessible window (not drawn yet?)'
    assert obs['open-panel']['ok'] and obs['open-panel']['where']=='preview-ca9cbc8786144517b3a14ef57a90e08b'
    assert obs['open-panel']['owned_project_row'] and obs['open-panel']['open_enabled']
    assert obs['reopened']['ok'] and obs['reopened']['window']=='PreviewLab — PreviewLab.swift'
    assert obs['reopened-paused']['canvas_paused']
    final=obs['final'];assert final['ok'] and final['pid']==45749 and final['pin_identifier']=='pin.fill'
    assert final['preview_labels']==['Primary layers','Text and interaction','Layout edit']
    actions=[v for v in ui if v['kind']=='action']
    assert [v['args'].get('menu',v['args'].get('label')) for v in actions]==['Pin Preview','Pin Preview','File>Close Project','File>Open…','Open','Refresh Canvas']
    assert all(v['data']['ok'] and v['data']['result']['ok'] for v in actions)
    labels=[v.get('label') for v in ui]
    assert labels.index('after-project-close')<labels.index('after-close')<labels.index('open-panel')<labels.index('reopened')
    cleanup=next(v for v in events if v['event']=='cleanup-done')
    assert cleanup['main'] and cleanup['weak_slots_destroyed']==2 and not cleanup['helper_module_loaded']
    assert [v['stage'] for v in rows[-3:]]==['script-unloaded','session-detached','session-ended-no-target-termination']
    assert rows[-1]['source_restored']
    post=json.loads((root/'postflight.json').read_text())
    assert post['controller_available'] and post['executable']=='/Applications/Xcode.app/Contents/MacOS/Xcode'
    assert post['source_sha256']=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef'
    assert post['project_sha256']=='1ee671965dcfb221233970e970130946a1971a0b0d30625601e93440a60bcf45'
    return {'paired_native_setters':paired,'weak_alive_after_project_close':[1],'weak_alive_after_reopen':[1,2],'target_destruction_verified':False,'refresh_private_callbacks_instrumented':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);print(json.dumps(verify(p.parse_args().directory),indent=2))
