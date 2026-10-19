"""Owned helper-process settlement only, never native target UI qualification."""
from pathlib import Path
import datetime,hashlib,json,math
from phase_prerequisites import parsed,require as need,integer
from predictions import marker
H=lambda b:hashlib.sha256(b).hexdigest()
def number(v):return type(v) in [int,float] and math.isfinite(v) and v>=0

def rows_observed(root,v):
 p=Path(root);need(integer(v['pid']) and v['pid']>1,'parent pid')
 need(v['native_UI_execution'] is False and v['provider_target_UI_settlement_qualified'] is False and v['product_integration'] is False,'scope')
 need(type(v['rows']) is list and len(v['rows'])==2,'case count');total=0;pids=[]
 for mode,row in zip(['default','stoppable'],v['rows']):
  need(row['mode']==mode and row['folder']==mode and integer(row['pid']) and row['pid']>1 and row['pid']!=v['pid'],'owned child pid');pids.append(row['pid']);d=p/'owned-documents'/mode
  need(type(row['nonce']) is str and len(row['nonce'])==32 and all(c in '0123456789abcdef' for c in row['nonce']),'nonce')
  need({q.name for q in d.iterdir()}=={'ready.json','term.json','done.json','marker.raw'} and all(q.is_file() and not q.is_symlink() for q in d.iterdir()),'case inventory')
  ready=parsed((d/'ready.json').read_text());term=parsed((d/'term.json').read_text());done=parsed((d/'done.json').read_text())
  need(integer(ready['pid'],row['pid']) and integer(ready['ppid'],v['pid']) and ready['nonce']==row['nonce'] and integer(term['pid'],row['pid']) and term['nonce']==row['nonce'] and term['signal']=='SIGTERM' and integer(done['pid'],row['pid']) and done['nonce']==row['nonce'] and integer(done['intended_exit'],0),'owned source receipts')
  raw=(d/'marker.raw').read_bytes();need(raw==marker() and row['marker_sha256']==H(raw) and integer(row['marker_bytes'],1024),'complete marker bytes');total+=len(raw)
  need(row.get('unexpected_success',False) is False and row['error_name']=='AbortError' and row['error_code']=='ABORT_ERR' and row['stderr']=='','provider error')
  need(type(row['stdout']) is str and len(row['stdout'])<=16384,'child stream')
  if row['stdout']:
   stream=parsed(row['stdout']);need(integer(stream['owned_child_pid'],row['pid']) and stream['nonce']==row['nonce'],'captured child identity')
  need(all(number(row[k]) for k in ['abort_at','settled_at','exit_at','close_at']),'event clock')
  need(integer(row['exit_code'],0) and integer(row['close_code'],0) and row['exit_signal'] is None and row['close_signal'] is None and row['signal_code_at_settlement'] is None,'actual exit/close')
  if mode=='default':need(row['abort_at']<=row['settled_at']<row['exit_at']<=row['close_at'] and row['marker_present_at_settlement'] is False and row['exit_code_at_settlement'] is None and row['exit_seen_at_settlement'] is False and row['close_seen_at_settlement'] is False,'default early settlement')
  else:need(row['abort_at']<row['exit_at']<=row['close_at']<=row['settled_at'] and row['marker_present_at_settlement'] is True and integer(row['exit_code_at_settlement'],0) and row['exit_seen_at_settlement'] is True and row['close_seen_at_settlement'] is True,'stoppable terminal settlement')
 need(len(set(pids))==2 and {q.name for q in (p/'owned-documents').iterdir()}=={'default','stoppable'},'distinct owned cases')
 return {'marker_bytes_compared':total,'marker_padding_bytes':72,'marker_tail_bytes':1856,'default_abort_settles_before_owned_exit_and_late_write':True,'stoppable_abort_settles_after_owned_close':True,'shipped_helper_call_instrumented':True,'native_UI_execution':False,'provider_target_UI_settlement_qualified':False,'canvas_qualified':False}

def observed(root):
 p=Path(root)
 for n,h in parsed((p/'approved-pins.json').read_text()).items():need(H((p/n).read_bytes())==h,'approved pin')
 plan=parsed((p/'plan.json').read_text());rea=parsed((p/'rea-identity.json').read_text());need(plan['library_sha256']==H((p/'shipped/ExecFileOutput.js').read_bytes())==rea['sha256'] and rea['closed'] is True and rea['format']=='javascript','provider artifact')
 run=parsed((p/'execution-record.json').read_text());outer=parsed((p/'execution-outer.json').read_text())
 need(integer(outer['exit'],0) and integer(outer['executions'],1) and run['error'] is None and run['command']==plan['node_path'] and run['args']==['/private/tmp/rea-provider-settlement-20261019/probe.mjs'],'execution binding')
 record=run['record'];report=record['report'];need(report['kind']=='complete' and integer(report['target_code'],0) and report['failure'] is None and report['drained'] is True and integer(report['remaining_observed'],0) and record['emergencyClosed'] is False and record['privateAbortRequested'] is False,'observed lifecycle')
 for name in ['stdout','stderr']:
  raw=record[name].encode();need(integer(record[name+'Bytes'],len(raw)) and record[name+'Sha256']==H(raw),'captured stream hash')
 need(record['stderr']=='','root diagnostics');v=parsed(record['stdout']);need(v['environment']==plan['node_environment'] and v['library_sha256']==plan['library_sha256'],'runtime/source identity')
 start=parsed((p/'started.json').read_text());deadline=datetime.datetime(2026,10,19,17,30,tzinfo=datetime.timezone.utc)
 need(start['deadline_utc']==outer['deadline_utc']=='2026-10-19T17:30:00Z' and datetime.datetime.fromisoformat(start['at'])<datetime.datetime.fromisoformat(outer['completed_at'])<deadline,'deadline')
 return rows_observed(p,v)
if __name__=='__main__':print(json.dumps(observed(Path(__file__).resolve().parent),sort_keys=True))
