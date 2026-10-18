"""Replay bounded planner verification event logs; no controller execution."""
def summarize(rows):
 pending=None;files=bytes_=0;ids=[];seconds=0;result=None
 for row in rows:
  if not isinstance(row,dict):raise ValueError('row')
  event=row.get('event')
  if event=='verify_start':
   if pending is not None or result is not None:raise ValueError('start order')
   if not isinstance(row.get('run_id'),str) or not row['run_id']:raise ValueError('identity')
   if any(type(row.get(k)) is not int or row[k]<0 for k in ['declared_files','declared_bytes']):raise ValueError('counts')
   pending=row
  elif event=='verify_finish':
   if pending is None or row.get('run_id')!=pending['run_id']:raise ValueError('finish binding')
   if row.get('valid') is not True or row.get('external_anchor_matches') is not True:raise ValueError('integrity')
   t=row.get('seconds')
   if type(t) not in (int,float) or not 0<=t<20:raise ValueError('time')
   seconds+=t;files+=pending['declared_files'];bytes_+=pending['declared_bytes'];ids.append(pending['run_id']);pending=None
  elif event=='graph_result':
   if pending is not None or result is not None:raise ValueError('result order')
   if row.get('all_milestones_complete') is not False:raise ValueError('acceptance')
   result=row
  else:raise ValueError('unknown event')
 if pending is not None or result is None:raise ValueError('incomplete')
 return {'verification_calls':len(ids),'unique_runs':len(set(ids)),'declared_files_across_calls':files,'declared_bytes_across_calls':bytes_,'verification_seconds':seconds,'result':result}
