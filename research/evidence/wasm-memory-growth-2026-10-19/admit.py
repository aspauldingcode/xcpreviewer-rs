"""Fail-closed non-browser memory lifecycle assay admission."""
from pathlib import Path
import datetime
import hashlib
import json
from phase_prerequisites import parsed,require as need,integer
from predictions import expected,NAMES
H=lambda b:hashlib.sha256(b).hexdigest()
MODULE='970468fb9b02b07bd628c530877571db3d2ca614f73e8498b6fdd40455b3c0c6'
def result(root,value):
 p=Path(root)
 need(type(value) is dict and integer(value.get('pid')) and 1<value['pid']<=2147483647,'pid')
 need(value['module_sha256']==MODULE and integer(value['module_bytes'],80),'module')
 need(value['imports']==[] and value['exports']==[{'name':'memory','kind':'memory'},{'name':'store8','kind':'function'},{'name':'grow','kind':'function'}],'module exports')
 need(all(value[k] is False for k in ['browser_execution','native_canvas_evidence','product_integration']),'scope flags')
 need(type(value['rows']) is list and len(value['rows'])==5,'rows')
 names=set();total=0
 for name,row in zip(NAMES,value['rows']):
  need(row['stage']==name and row['file']==name+'.raw','stage binding');f=p/'owned-output'/row['file'];need(f.is_file() and not f.is_symlink(),'raw file');raw=f.read_bytes();prediction=expected(name)
  need(integer(row['bytes'],len(prediction)) and len(raw)==len(prediction) and raw==prediction and row['sha256']==H(raw),'complete independent bytes');names.add(f.name);total+=len(raw)
 need({q.name for q in (p/'owned-output').iterdir()}==names,'output inventory')
 events=value['events'];need(type(events) is list and len(events)==4,'events')
 for i,name in enumerate(['zero-grow','positive-grow']):
  row=events[i];need(row['phase']==name and integer(row['return_value'],1) and integer(row['new_buffer_bytes'],65536 if i==0 else 131072),'growth value')
  need(row['buffer_changed'] is True and integer(row['old_buffer_bytes'],0) and integer(row['old_view_bytes'],0) and row['data_view_error']=='TypeError' and row['stale_read_undefined'] is True and row['stale_write_affected_current'] is False,'detached views')
 row=events[2];need(row['phase']=='js-failed-grow' and row['error']=='RangeError','JS failure')
 row=events[3];need(row['phase']=='wasm-failed-grow' and integer(row['return_value'],-1),'WASM failure')
 for row in events[2:]:need(row['buffer_same'] is True and integer(row['view_bytes'],131072) and integer(row['new_buffer_bytes'],131072),'failed growth identity')
 return {'all_bytes_compared':total,'successful_growths':2,'failed_growths':2,'zero_growth_detaches':True,'failed_growth_preserves_buffer':True,'stale_dataview_rejected':True,'stale_typedarray_write_ineffective':True,'browser_verified':False,'second_engine_verified':False,'non_Apple_OS_verified':False,'canvas_qualified':False}
def admit(root):
 p=Path(root)
 for n,h in parsed((p/'approved-pins.json').read_text()).items():need(H((p/n).read_bytes())==h,'approved pin')
 need(H((p/'probe.wasm').read_bytes())==MODULE,'module identity')
 before=parsed((p/'runtime-before.json').read_text());rea=parsed((p/'rea-identity.json').read_text())
 need(rea['sha256']==before['sha256'] and rea['path']==before['path'] and rea['architecture']=='arm64' and rea['closed'] is True,'REA runtime binding')
 run=parsed((p/'execution.json').read_text());need(integer(run['exit'],0) and run['stderr']=='' and run.get('timeout',False) is False and integer(run['executions'],1),'bounded execution')
 start=parsed((p/'started.json').read_text());deadline=datetime.datetime(2026,10,19,17,0,tzinfo=datetime.timezone.utc)
 need(start['deadline_utc']==run['deadline_utc']=='2026-10-19T17:00:00Z' and datetime.datetime.fromisoformat(start['at'])<datetime.datetime.fromisoformat(run['completed_at'])<deadline,'fixed deadline')
 value=parsed(run['stdout']);env=value['environment']
 need(env==before['environment'] and env['platform']=='darwin' and env['arch']=='arm64','runtime identity')
 return result(p,value)
if __name__=='__main__':print(json.dumps(admit(Path(__file__).resolve().parent),sort_keys=True))
