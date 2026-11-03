"""Verify observed removed-file filtering only; propagation absence is not success."""
from pathlib import Path
import argparse,json

def verify(r,auxiliary=False):
 rows=[json.loads(x) for x in (r/'events.jsonl').read_text().splitlines()];assert rows
 assert all(a['time_ns']<=b['time_ns'] for a,b in zip(rows,rows[1:]))
 assert not any(x['stage'] in ['failure','cleanup-unconfirmed','unload-error','auxiliary-cleanup-skipped-concurrent-edit','restore-skipped-concurrent-recreation'] for x in rows)
 assert not any(x['stage']=='script' and x['message']['type']=='error' for x in rows)
 payloads=[(i,x['message']['payload']) for i,x in enumerate(rows) if x['stage']=='script' and x['message']['type']=='send']
 def event(name):return [(i,v) for i,v in payloads if v['event']==name]
 ready=event('hooks-ready');assert len(ready)==1
 assert ready[0][1]['xcode_uuid']=='25c99c664185307188e31ab474573a10' and ready[0][1]['scenes_uuid']=='afaf513ac1153755840e1d82b40e7d93'
 deleted=[(i,v) for i,v in enumerate(rows) if v['stage']=='source-deleted'];assert len(deleted)==1 and deleted[0][1]['absent'] is True
 restored=[(i,v) for i,v in enumerate(rows) if v['stage']=='source-restored'];assert len(restored)==1
 assert event('phase-ack')[0][1]['label']=='baseline' or auxiliary
 assert not [v for _,v in payloads if v.get('phase')=='baseline' and v['event']=='removed-files-block']
 selected=[(i,v) for i,v in event('removed-files-block') if deleted[0][0]<i<restored[0][0] and v['phase']=='removed'];assert len(selected)==1
 bi,b=selected[0];scope=[(i,v) for i,v in payloads if v.get('id')==b['id']]
 assert [v['event'] for _,v in scope]==['workspace-handler-enter','removed-files-block','removed-filter-enter','removed-filter-return','workspace-handler-return']
 assert len({v['thread'] for _,v in scope})==1 and all(deleted[0][0]<i<restored[0][0] for i,_ in scope)
 assert next(v for _,v in scope if v['event']=='removed-filter-enter')['caller_offset']=='0x249a0c'
 assert not any(v['event'] in ['workspace-removed-enter','editor-removed-enter','scene-update-enter','coalescer-enter'] for _,v in scope)
 wait=[v for v in rows if v['stage']=='removed-wait-ended'];assert len(wait)==1 and wait[0]['workspace_removed_observed'] is False
 cleanup=event('cleanup-done');assert len(cleanup)==1 and cleanup[0][1]['total_events']<1000
 assert len([x for x in rows if x['stage']=='script-unloaded'])==len([x for x in rows if x['stage']=='session-detached'])==1
 assert rows[-1]['stage']=='session-ended' and rows[-1]['source_restored'] is True
 if auxiliary:
  build=[v for v in rows if v['stage']=='cli-build-ended'];assert len(build)==1 and build[0]['code']==0 and build[0]['log_mentions_dependency'] is True
  assert len([v for v in rows if v['stage']=='auxiliary-cleaned' and v['project_restored'] and v['dependency_absent']])==1
  assert rows[-1]['project_restored'] and rows[-1]['auxiliary_absent']
 return {'actual_file_deletion':True,'native_removed_block_and_filter_interval':True,'workspace_removed_update_exercised':False,'editor_removed_update_exercised':False,'filter_result_contents_or_reason_verified':False,'native_resource_release_verified':False,'auxiliary_cli_build':auxiliary}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--auxiliary',action='store_true');a=p.parse_args();print(json.dumps(verify(a.directory,a.auxiliary)))
