"""Recorded paired input controls; successful probe coverage is not refresh parity."""
from pathlib import Path
import argparse,json
from verify import verify

def verify_input(r):
 result=verify(r);assert result['native_missing_optional_type_and_zero_candidates']
 rows=[json.loads(x) for x in (r/'events.jsonl').read_text().splitlines()]
 payloads=[(i,x['message']['payload']) for i,x in enumerate(rows) if x['stage']=='script' and x['message']['type']=='send']
 modified=[i for i,x in enumerate(rows) if x['stage']=='source-modified-control'];restored=[i for i,x in enumerate(rows) if x['stage']=='source-modified-control-restored'];deleted=[i for i,x in enumerate(rows) if x['stage']=='source-deleted'];assert len(modified)==len(restored)==len(deleted)==1 and modified[0]<restored[0]<deleted[0]
 for phase,lower,upper in [('modified-control',modified[0],restored[0]),('restore-control',restored[0],deleted[0])]:
  entries=[(i,v) for i,v in payloads if v['event']=='removed-filter-enter' and v['phase']==phase];assert len(entries)==1
  _,entry=entries[0];scope=[(i,v) for i,v in payloads if v.get('id')==entry['id']]
  assert [v['event'] for _,v in scope]==['workspace-handler-enter','removed-filter-enter','filter-input-count','filter-optional-type','filter-candidate-count','filter-thunkable-result','filter-predicate-result','removed-filter-return','workspace-handler-return']
  assert all(lower<i<upper for i,_ in scope) and len({v['thread'] for _,v in scope})==1
  def event(n):return next(v for _,v in scope if v['event']==n)
  assert entry['caller_image']=='PreviewsXcode' and entry['caller_offset']=='0x249c60'
  assert event('filter-input-count')['count_register']==event('filter-candidate-count')['count_register']=='0x1'
  assert event('filter-optional-type')['present'] is True
  assert event('filter-thunkable-result')['value']==1 and event('filter-predicate-result')['value']==0
 result.update(typed_modified_and_restored_controls=2,selected_scene_propagation_exercised=False,payload_paths_decoded=False)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();print(json.dumps(verify_input(a.directory)))
