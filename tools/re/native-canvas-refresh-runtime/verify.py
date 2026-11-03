"""Assert bounded manual-refresh absence plus real-file positive probe controls."""
import argparse,json
from pathlib import Path
ORIGINAL='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef'
LABELS=['idle-start','idle-end','refresh-start','refresh-return','refresh-settled','edit','edit-settled','restore','restore-settled']

def verify(root,button):
    rows=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    assert all(a['time_ns']<=b['time_ns'] for a,b in zip(rows,rows[1:]))
    assert not any(v['stage'] in ['failure','unload-error','detach-error','restore-skipped-concurrent-edit'] for v in rows)
    phases=[v for v in rows if v['stage']=='phase'];assert [v['label'] for v in phases]==LABELS
    markers={v['label']:v for v in phases};assert markers['idle-end']['time_ns']-markers['idle-start']['time_ns']>=3_000_000_000
    assert all(v['source_sha256']==ORIGINAL for v in phases if v['label'] not in ['edit','edit-settled'])
    assert markers['edit']['source_sha256']==markers['edit-settled']['source_sha256']!=ORIGINAL
    if button:assert markers['refresh-settled']['time_ns']-markers['refresh-return']['time_ns']>=8_000_000_000
    events=[v['message']['payload'] for v in rows if v['stage']=='script'];ready=next(v for v in events if v['event']=='hooks-ready')
    assert ready['scenes_uuid']=='afaf513ac1153755840e1d82b40e7d93' and ready['ui_uuid']=='0d87b0e2f4453035a9b6b1cf8230e015'
    active={};stack=[];counts={'edit':0,'restore':0};helpers={'edit':0,'restore':0};phase='startup'
    for row in rows:
        if row['stage']=='phase':phase=row['label'];continue
        if row['stage']!='script':continue
        v=row['message']['payload'];name=v['event']
        if name=='hooks-ready':continue
        assert phase in ['edit','restore'],'Unexpected selected-method callback outside source-change phases'
        if name.endswith('-enter'):
            assert v['id'] not in active
            if name=='instance-assignment-helper-enter':
                assert stack and stack[-1][0]=='preview-update-enter'
                assert active[stack[-1][1]]['thread']==v['thread'] and v['caller_offset']=='0x3f978'
                helpers[phase]+=1
            else:assert name=='preview-update-enter';counts[phase]+=1
            active[v['id']]=v;stack.append((name,v['id']))
        else:
            enter=active.pop(v['id']);assert name==enter['event'].replace('-enter','-return')
            assert stack.pop()==(enter['event'],v['id'])
    assert not active and not stack
    assert all(counts[k]>0 and counts[k]==helpers[k] for k in counts)
    assert [v['stage'] for v in rows[-3:]]==['script-unloaded','session-detached','session-ended-no-target-termination'] and rows[-1]['source_restored']
    ui=json.loads((root/'ui.json').read_text());obs={v['label']:v['data'] for v in ui if v['kind']=='observe'}
    assert obs['baseline']['ok'] and obs['baseline']['pid']==45749 and obs['baseline']['window']=='PreviewLab — PreviewLab.swift'
    actions=[v for v in ui if v['kind']=='action'];assert len(actions)==1
    action=actions[0]
    if button:
        assert obs['baseline']['canvas_paused'] and obs['baseline']['refresh_enabled']
        assert action['args']['op']=='press' and action['args']['label']=='Refresh Canvas' and action['data']['ok'] and action['data']['result']['ok']
        assert obs['refreshed']['preview_labels']==['Primary layers','Text and interaction','Layout edit']
    else:
        assert action['args']['menu']=='Editor>Canvas>Refresh Canvas' and action['data']['ok'] is False
        assert action['data']['error']=='no menu item "Refresh Canvas" under AXMenuItem "Canvas" ="On"'
    final=obs['restored'];assert final['ok'] and final['pin_identifier']=='pin.fill' and final['preview_labels']==['Primary layers','Text and interaction','Layout edit']
    return {'manual_action':'native AXPress acknowledged' if button else 'menu-path executor failed; not a manual refresh','selected_method_callbacks_before_file_edit':0,'source_edit_update_pairs':counts['edit'],'source_restore_update_pairs':counts['restore'],'nested_assignment_pairs':helpers,'rendered_pixels_verified':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--button',action='store_true');a=p.parse_args();print(json.dumps(verify(a.directory,a.button),indent=2))
