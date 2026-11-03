"""Assertions over executed public-SDK traces; never Canvas parity proof."""
from pathlib import Path
import argparse,json
MODES=['normal','cancel-inflight','cancel-pending']
OWNER_MODES=['release-inflight','release-pending']
def verify(root,owner_release=False):
 result={};pids=[]
 for mode in MODES+(OWNER_MODES if owner_release else []):
  records=[json.loads(x) for x in (root/(mode+'.stdout')).read_text().splitlines()];d=records[-1];rows=d['trace'];assert records[:-1]==rows
  status=json.loads((root/(mode+'.result.json')).read_text());assert status['code']==0 and status['timeout'] is False and status['pid']==d['pid'];pids.append(d['pid'])
  assert d['mode']==mode and d['peer_pid']==d['pid'] and d['server_pid']==0
  assert d['runtime']=={'path':'/usr/lib/system/libxpc.dylib','uuid':'c40fcae87a173d8287cb3da4802adef1'}
  assert d['private_canvas_invoked'] is False and d['target_resource_settlement_verified'] is False
  assert d['callbacks']==d['invalid_events']==d['capture_drops']==1 and d['queue_mismatches']==0 and d['fd_closed'] is True and d['quiet_window_ms']==100
  assert [v['seq'] for v in rows]==list(range(1,len(rows)+1)) and all(a['time_ns']<=b['time_ns'] for a,b in zip(rows,rows[1:]))
  def row(name):
   found=[v for v in rows if v['event']==name];assert len(found)==1;return found[0]
  def order(*names):assert [row(n)['seq'] for n in names]==sorted(row(n)['seq'] for n in names)
  order('capture-created','peer-request','client-peer-query','callback-blocked','main-observed-blocked','callback-release-signal','callback-returning','capture-deinit','capture-cleanup-observed','observation-complete')
  assert rows[-1]['event']=='observation-complete'
  assert row('capture-created')['fd']==row('capture-deinit')['fd'] and row('capture-deinit')['close_result']==0
  assert row('callback-blocked')['capture_fd_open'] and row('callback-returning')['capture_fd_open'] and row('callback-returning')['reply_valid']
  assert row('main-observed-blocked')['capture_fd_open'] and row('main-observed-blocked')['capture_drops']==0
  assert row('capture-cleanup-observed')['capture_drops']==1 and row('capture-cleanup-observed')['fd_closed']
  assert row('callback-blocked')['thread_id']==row('callback-returning')['thread_id']!=row('main-observed-blocked')['thread_id']
  assert row('client-peer-query')['reported_pid']==0 and row('client-peer-query')['accepted_peer_pid']==d['pid']
  releasing=mode in OWNER_MODES
  if releasing:
   assert d['caller_client_reference_released_while_blocked'] is True and d['invalid_event_observed'] is True
   order('main-observed-blocked','client-owner-release-begin','client-owner-release-returned-blocked','callback-release-signal')
   released=row('client-owner-release-returned-blocked');assert released['capture_drops']==0 and released['capture_fd_open']
   assert released['thread_id']==row('main-observed-blocked')['thread_id']
  elif 'caller_client_reference_released_while_blocked' in d:assert d['caller_client_reference_released_while_blocked'] is False
  if mode in ['cancel-pending','release-pending']:
   assert d['invalid_before'] and d['invalid_after'] and not d['dictionary_before'] and not d['marker_before'] and not d['marker_after']
   order('peer-request','pending-cancel-begin','pending-cancel-returned','main-observed-blocked')
   order('pending-cancel-begin','callback-blocked','callback-returning','capture-cleanup-observed','late-peer-reply-submit','observation-complete')
   order('pending-cancel-begin','client-invalid','late-peer-reply-submit')
  else:
   assert d['dictionary_before'] and d['marker_before'] and d['marker_after'] and not d['invalid_before'] and not d['invalid_after']
   order('peer-reply-submit','callback-blocked','callback-returning','client-invalid')
   if mode in ['cancel-inflight','release-inflight']:
    order('main-observed-blocked','cancel-begin','cancel-returned-blocked','callback-release-signal')
    if releasing:order('cancel-returned-blocked','client-owner-release-begin')
    assert row('cancel-returned-blocked')['capture_drops']==0 and row('cancel-returned-blocked')['capture_fd_open']
   else:order('capture-cleanup-observed','cancel-after-callback','client-invalid')
  result[mode]={'native_sdk_assertions_passed':True,'owned_capture_fd_cleanup_observed':True,'client_peer_pid_query_available':False,'canvas_resource_settlement_verified':False,'caller_client_ref_released_during_callback':releasing}
 assert len(set(pids))==3+(2 if owner_release else 0)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--owner-release',action='store_true');a=p.parse_args();print(json.dumps(verify(a.directory,a.owner_release),indent=2))
