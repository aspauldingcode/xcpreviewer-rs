"""Recorded project-membership control, scoped separately from filesystem deletion."""
from pathlib import Path
import argparse,json

def verify_membership(r):
 rows=[json.loads(x) for x in (r/'events.jsonl').read_text().splitlines()];assert rows
 assert all(a['time_ns']<=b['time_ns'] for a,b in zip(rows,rows[1:]))
 assert not any(x['stage'] in ['failure','cleanup-unconfirmed','unload-error','cli-build-timeout','auxiliary-cleanup-skipped-concurrent-edit'] for x in rows)
 assert not any(x['stage']=='script' and x['message']['type']=='error' for x in rows)
 payloads=[(i,x['message']['payload']) for i,x in enumerate(rows) if x['stage']=='script' and x['message']['type']=='send']
 def stage(n):
  values=[(i,v) for i,v in enumerate(rows) if v['stage']==n];assert len(values)==1;return values[0]
 ready=[v for _,v in payloads if v['event']=='hooks-ready'];assert len(ready)==1
 assert ready[0]['xcode_uuid']=='25c99c664185307188e31ab474573a10' and ready[0]['scenes_uuid']=='afaf513ac1153755840e1d82b40e7d93' and ready[0]['path_identity_getters'] is True
 _,build=stage('cli-build-ended');assert build['code']==0 and build['log_mentions_dependency'] is True
 lower,change=stage('project-membership-removed');upper,restore=stage('project-membership-restored');assert change['file_present'] and change['file_bytes_match'] and restore['file_present'] and lower<upper
 assert not any(x['stage']=='source-deleted' for x in rows)
 selected=[(i,v) for i,v in payloads if v['event']=='removed-files-block' and lower<i<upper and v['phase']=='removed'];assert len(selected)==1
 _,block=selected[0];scope=[(i,v) for i,v in payloads if v.get('id')==block['id']]
 assert [v['event'] for _,v in scope]==['workspace-handler-enter','removed-files-block','removed-filter-enter','filter-input-count','filter-optional-type','filter-candidate-count','removed-filter-return','removed-filter-count-branch','workspace-handler-return']
 assert all(lower<i<upper for i,_ in scope) and len({v['thread'] for _,v in scope})==1
 def event(n):return next(v for _,v in scope if v['event']==n)
 assert event('filter-input-count')['count_register']=='0x1'
 obj=event('filter-optional-type');assert obj['present'] is False and obj['path_kind']=='auxiliary' and obj['getter_main'] and obj['getter_receiver_expected_family'] and obj['getter_read_available']
 assert event('filter-candidate-count')['count_register']==event('removed-filter-count-branch')['count_register']=='0x0'
 updates=[(i,v) for i,v in payloads if v['event']=='scene-update-enter' and v['phase']=='removed' and lower<i<upper];assert len(updates)==3 and len({v['id'] for _,v in updates})==3
 callers=[]
 for _,update in updates:
  other=[(i,v) for i,v in payloads if v.get('id')==update['id']];assert update['id']!=block['id']
  assert [v['event'] for _,v in other]==['workspace-handler-enter','coalescer-enter','coalescer-return','scene-update-enter','scene-update-return','workspace-handler-return']
  assert all(lower<i<upper for i,_ in other) and len({v['thread'] for _,v in other})==1
  c=next(v for _,v in other if v['event']=='coalescer-enter');callers.append(c['caller_offset']);assert c['caller_image']=='PreviewsXcode' and update['caller_image']=='PreviewsXcode' and update['caller_offset']=='0x24a070'
 assert sorted(callers)==['0x249b64','0x249d3c','0x249d3c']
 assert stage('removed-wait-ended')[1]['workspace_removed_observed'] is False
 assert stage('auxiliary-cleaned')[1]['project_restored'] and stage('auxiliary-cleaned')[1]['dependency_absent']
 assert stage('script-unloaded')[0]<stage('session-detached')[0]
 cleanup=[v for _,v in payloads if v['event']=='cleanup-done'];assert len(cleanup)==1 and cleanup[0]['total_events']<1000
 final=rows[-1];assert final['stage']=='session-ended' and final['source_restored'] and final['project_restored'] and final['auxiliary_absent']
 return {'membership_edit_while_auxiliary_present':True,'selected_filter_path_matches_auxiliary':True,'absent_optional_type_and_zero_candidates':True,'removed_location_propagation_exercised':False,'other_coalescer_scene_update_pairs':3,'other_event_reasons_decoded':False,'render_or_resource_release_verified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();print(json.dumps(verify_membership(a.directory)))
