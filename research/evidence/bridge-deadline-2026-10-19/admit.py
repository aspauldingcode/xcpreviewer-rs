"""Admit only owned socket evidence; never promote it to upstream/UI proof."""
from pathlib import Path
import json,hashlib,datetime

def need(v):
 if not v:raise ValueError('Owned broker deadline evidence rejected')
def parsed(raw):
 def pairs(items):
  out={}
  for k,v in items:need(k not in out);out[k]=v
  return out
 def constant(v):raise ValueError('Nonfinite JSON')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
def admit(root):
 p=Path(root);outer=parsed((p/'execution.json').read_text());need(type(outer['exit']) is int and outer['exit']==0 and outer['stderr']=='' and type(outer['executions']) is int and outer['executions']==1 and outer['native_UI_execution'] is False)
 need(outer['deadline_utc']=='2026-10-19T09:15:00Z' and datetime.datetime.fromisoformat(outer['completed_at'])<datetime.datetime(2026,10,19,9,15,tzinfo=datetime.timezone.utc))
 data=parsed(outer['stdout']);need(data['source_sha256']==hashlib.sha256((p/'xcodebridge.py').read_bytes()).hexdigest() and data['extracted_definitions']==['BrokerClient','identity','manage','validate_request'])
 need(data['native_UI_execution'] is False and data['native_cleanup_block_removed'] is False and data['upstream_Apple_request'] is False)
 rows=data['records'];need(type(rows) is list and len(rows)==2 and [x['case'] for x in rows]==['bound_endpoint_false_responsiveness','caller_timeout_late_server_effect'])
 a,b=rows;need(type(a['owned_pid']) is int and 1<a['owned_pid']<2**31 and type(b['owned_pid']) is int and a['owned_pid']==b['owned_pid'])
 need(a['running'] is True and a['responsive_field'] is True and a['actual_status_response_verified'] is False and a['client_error']=='ConnectionRefusedError' and a['socket_cleanup_verified'] is True)
 need(b['caller_error']=='timeout' and b['status_response_verified'] is True and b['requests']==[{'method':'status','params':{}},{'method':'tools/call','params':{'name':'XcodeListWindows','arguments':{}}}])
 need(b['zero_before_server_effect'] is True and b['late_effect_hex']==b'owned-late-effect\n'.hex() and b['server_joined'] is True and b['socket_cleanup_verified'] is True and b['upstream_Apple_request'] is False)
 events=b['journal'];need(type(events) is list and [x['event'] for x in events]==['server_received','caller_timeout','zero_before_terminal_server','server_effect'])
 times=[x['at_ns'] for x in events];need(all(type(x) is int and x>0 for x in times) and all(x<y for x,y in zip(times,times[1:])))
 return {'owned_socket_controls':2,'metadata_responsive_false_positive_reproduced':True,'caller_timeout_precedes_late_mock_effect':True,'marker_bytes_compared':18,'owned_server_join_and_socket_cleanup_verified':True,'native_UI_execution':False,'upstream_Apple_settlement_qualified':False,'native_cleanup_block_removed':False}
if __name__=='__main__':print(json.dumps(admit(Path(__file__).resolve().parent)))
