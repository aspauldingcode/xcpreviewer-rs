"""Verify a failed action qualification is retained; this is not a native rerun."""
from pathlib import Path
import argparse,json,re

def verify(root):
    s=json.loads((root/'observations.json').read_text());post=json.loads((root/'postflight.json').read_text())
    assert s['preflight']['ok'] and s['preflight']['pid']==45749 and s['preflight']['window']=='PreviewLab — PreviewLab.swift'
    tab=next(e for e in s['preflight']['controls'] if e['label']=='Text and interaction');full=next(e for e in s['preflight']['controls'] if e['label']=='Full screen')
    assert s['tab_action']['ok'] is False and 'offers no AXPress' in s['tab_action']['error']
    a=s['visual_action'];assert a['ok'] and a['result']['mechanism']=='HID (real pointer)'
    match=re.fullmatch(r'clicked (\d+),(\d+) in Xcode',a['result']['detail']);assert match
    x,y=map(int,match.groups());inside=lambda f:f[0]<=x<f[0]+f[2] and f[1]<=y<f[1]+f[3]
    assert inside(full['frame']) and not inside(tab['frame'])
    assert (x,y)!=(s['requested_visual_action']['x'],s['requested_visual_action']['y'])
    assert s['after_visual']['ok'] is False and s['after_visual_screenshot']['ok'] is False
    assert s['activation']['ok'] and s['after_activation']['ok'] is False
    assert s['open_recovery'][0]['data']['ok'] is False and s['open_recovery'][0]['data']['error']=='no menu bar exposed'
    assert s['fullscreen_key']['ok'] and s['after_fullscreen_key']['ok'] is False
    assert not any(s[k] for k in ['interaction_exercised','counter_value_observed','interactive_state_preservation_verified','window_mode_restored_verified','source_or_project_modified'])
    assert s['session_metadata']['screen_locked_field'] is None and not s['session_metadata']['lock_state_established']
    assert post['controller_available'] and post['old_pid_45749_present'] is False
    assert post['current_xcode_main_processes']==['64394 /Applications/Xcode.app/Contents/MacOS/Xcode']
    crash=json.loads((root/'crash-summary.json').read_text());assert crash['pid']==45749 and crash['exception_type']=='EXC_BAD_ACCESS' and crash['exception_signal']=='SIGSEGV'
    assert not crash['causation_verified'] and not crash['prior_instrumentation_role_known']
    target=json.loads((root/'new-target.json').read_text());assert target['app_lookup'][0]['pid']==45749 and target['window_lookup'][0]['pid']==64394 and target['window_lookup'][0]['title']=='Welcome to Xcode'
    assert target['accessibility']['ok'] is False
    recovery=json.loads((root/'launchservices-recovery.json').read_text());assert recovery['returncode']==0 and recovery['verified_pre_request_pid']==64394
    window=recovery['settled_inventory']['windows'];assert len(window)==1 and window[0]['pid']==64394 and window[0]['title']=='PreviewLab — PreviewLab.swift'
    assert window[0]['frame']==[23,33,1401,902] and not recovery['canvas_state_or_counter_verified']
    assert post['source_sha256']=='128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef'
    assert post['project_sha256']=='1ee671965dcfb221233970e970130946a1971a0b0d30625601e93440a60bcf45'
    return {'reported_click':{'x':x,'y':y},'reported_click_inside_fullscreen_area':True,'requested_tab_not_clicked_by_receipt':True,'counter_interaction_verified':False,'ui_recovery_verified':False,'old_target_crash_report_confirmed':True,'new_target_pid':64394,'tool_identity_mismatch_observed':True,'source_project_original':True,'owned_project_window_title_restored':True,'canvas_state_restored_verified':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);print(json.dumps(verify(p.parse_args().directory),indent=2))
