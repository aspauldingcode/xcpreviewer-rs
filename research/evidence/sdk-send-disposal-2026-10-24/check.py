from pathlib import Path
import subprocess,json,hashlib
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(name,args,seconds):
 p=subprocess.run(args,capture_output=True,timeout=seconds);(w/(name+'.stdout')).write_bytes(p.stdout);(w/(name+'.stderr')).write_bytes(p.stderr)
 if p.returncode:print((p.stdout+p.stderr).decode())
 p.check_returncode();return p.stdout
abi=r/'research/evidence/mach2-invocation-2026-10-20';seal=json.loads((abi/'seal.json').read_text())
for f in seal['files']:assert sha(abi/f['path'])==f['sha256']
proof=json.loads((abi/'abi-proof.json').read_text());assert run('kernel-release',['uname','-r'],5).decode().strip()==proof['kernel_release'];assert proof['kernel_source_version'] in run('kernel-version',['uname','-v'],5).decode()
run('build',['python3',str(w/'build.py')],65)
outputs=[]
for mode in ['normal','cancel']:
 raw=run(mode+'-replay',[str(w/'probe'),mode],8);row=json.loads(raw)
 assert row['mach2_original_image']=={'path':'/usr/lib/system/libsystem_kernel.dylib','uuid':proof['runtime_image_uuid']}
 assert row['cancel_image']['uuid']==row['reply_image']['uuid']=='c40fcae87a173d8287cb3da4802adef1'
 assert row['request_received'] and row['callback_received'] and row['capture_alive_before_operation'] and row['capture_dropped_after_callback_within_1s'] and row['capture_drops']==1
 assert row['callbacks_in_observation_window']==1 and row['quiet_window_completed'] and not row['queue_mismatches'] and not row['exceptions']
 observations=row.pop('send_observations');assert row['trace_total_started']<row['trace_capacity']==512;assert len(observations)==row['trace_total_started'] and all(x['complete'] for x in observations)
 marker=[x for x in observations if x['owned_marker']];sends=[x for x in marker if x['api'] in [1,2]];destroys=[x for x in marker if x['api']==3]
 if mode=='normal':
  assert row['reply_dictionary'] and row['owned_marker_matches'];assert len(sends)==1 and sends[0]['api']==2 and sends[0]['phase']==1 and sends[0]['result']==0 and sends[0]['options']&1 and not sends[0]['options']&2 and sends[0]['send_size']==88
  assert sends[0]['caller_image']=={'path':'/usr/lib/system/libdispatch.dylib','uuid':'f071efe4299f3089acc40025b8ffb52a'} and sends[0]['caller_offset']==0x20784
  assert sends[0]['remote']==sends[0]['packed_remote']
  assert sends[0]['bits']&255==row['mach_constants']['move_send_once'];assert len(destroys)==1 and destroys[0]['remote']==0 and destroys[0]['caller_offset']==0x7ecc and destroys[0]['caller_image']=={'path':'/usr/lib/system/libxpc.dylib','uuid':'c40fcae87a173d8287cb3da4802adef1'}
 else:
  assert row['reply_invalid'] and row['late_peer_reply_submitted'];assert not sends and len(destroys)==1;d=destroys[0]
  assert d['caller_offset']==0x72cc
  assert d['phase']==2 and d['send_size']==88 and d['bits']&255==row['mach_constants']['move_send_once'] and d['queried']
  assert d['caller_image']=={'path':'/usr/lib/system/libxpc.dylib','uuid':'c40fcae87a173d8287cb3da4802adef1'}
  assert d['before_type_result']==d['before_refs_result']==0 and d['before_type']==row['mach_constants']['dead_name_type'] and d['before_refs']==1 and d['after_type_result']==row['mach_constants']['invalid_name']==15
 cleaned=[]
 for x in marker:
  clean={k:v for k,v in x.items() if k not in ['message_address','remote','packed_remote']};clean['remote_name_present']=x['remote']!=0
  if x['api']==3:clean['result']=None # void destruction call is not a kernel-result value.
  cleaned.append(clean)
 row['marker_observations']=cleaned;row['all_completed_observer_rows']=len(observations);row['scope_no_marker_send_in_observed_wrappers']=not sends;row['local_dead_name_retirement_observed']=mode=='cancel';row['global_rights_settlement_proven']=False
 outputs.append(row);(w/(mode+'-sanitized.json')).write_text(json.dumps(row,indent=2)+'\n')
context={'abi_predecessor':str(abi.relative_to(r)),'abi_predecessor_seal_sha256':sha(abi/'seal.json'),'kernel_source_header':proof['source_header'],'kernel_source_implementation':proof['source_implementation'],'kernel_version':proof['kernel_source_version'],'libsystem_kernel_uuid':proof['runtime_image_uuid'],'libxpc_uuid':'c40fcae87a173d8287cb3da4802adef1','sdk_headers':{}}
sdk=Path(subprocess.check_output(['xcrun','--show-sdk-path']).decode().strip())
for name in ['message.h','port.h','mach_port.h','kern_return.h']:context['sdk_headers'][name]=sha(sdk/'usr/include/mach'/name)
(w/'abi-context.json').write_text(json.dumps(context,indent=2)+'\n')
print('Normal marked reply: observed Mach2 send-only success. Canceled late marked reply: SDK destruction, one local dead-name reference then invalid name; no marked send in observed wrappers. No global/private target settlement claim.')

run('caller-source',['python3',str(w/'source-verify.py')],60)
