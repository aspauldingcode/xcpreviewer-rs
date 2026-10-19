"""Exact core-memory admission; explicitly excludes JavaScript host-view semantics."""
from pathlib import Path
import datetime,hashlib,json
from phase_prerequisites import parsed,require as need,integer
from predictions import NAMES,expected
from container_control import docker_command
H=lambda b:hashlib.sha256(b).hexdigest()
NODE=Path('/Users/8amps/xcpreviewer-rs/research/evidence/wasm-memory-growth-2026-10-19')
NODE_SEAL='1d33cf1b2cbe14f364e7647671de91e5581d8583426be701e39ca45c377dcaa6'
def rows_observed(p,v):
 p=Path(p);need(integer(v['pid']) and 1<=v['pid']<=2147483647,'container pid');need(v['host_system']=='Linux' and v['architecture']=='aarch64' and v['wasmtime']=='49.0.0','runtime identity')
 for k,n in [('module_bytes',80),('imports',0),('module_min_pages',1),('module_max_pages',2),('store_memory_limit_bytes',196608),('fuel_per_call',100000)]:need(integer(v[k],n),'typed metadata:'+k)
 need(v['module_sha256']=='970468fb9b02b07bd628c530877571db3d2ca614f73e8498b6fdd40455b3c0c6','module identity')
 need(v['fresh_copy_reads'] is True and all(v[k] is False for k in ['js_host_view_semantics_measured','browser_verified','canvas_qualified','product_integration']),'scope')
 need(type(v['rows']) is list and len(v['rows'])==5,'row count');total=0
 for name,row in zip(NAMES,v['rows']):
  need(row['stage']==name and row['file']==name+'.raw','stage binding');q=p/'owned-output'/row['file'];need(q.is_file() and not q.is_symlink(),'file');raw=q.read_bytes();prediction=expected(name)
  need(integer(row['bytes'],len(prediction)) and raw==prediction and row['sha256']==H(raw),'complete independent bytes');total+=len(raw)
 need({q.name for q in (p/'owned-output').iterdir()}=={n+'.raw' for n in NAMES}|{'result.json'},'inventory')
 need(type(v['events']) is list and len(v['events'])==4,'event count')
 for index,name in enumerate(NAMES[1:]):
  e=v['events'][index];need(e['phase']==name and integer(e['pages'],1 if index==0 else 2),'growth pages')
  if index in [0,1]:need(integer(e['return_value'],1),'growth success')
  elif index==2:need(e['error']=='WasmtimeError','host rejection')
  else:need(integer(e['return_value'],-1),'WASM rejection')
 return {'independent_bytes_compared':total,'linux_core_memory_verified':True,'fresh_copy_reads':True,'js_host_view_semantics_measured':False,'browser_verified':False,'canvas_qualified':False}
def observed(root):
 p=Path(root)
 for n,h in parsed((p/'approved-pins.json').read_text()).items():need(H((p/n).read_bytes())==h,'approved pin')
 plan=parsed((p/'plan.json').read_text());need(plan['context']=='colima' and plan['image_identity']=={'id':plan['image'],'os':'linux','architecture':'arm64'},'image identity')
 need(plan['image']=='sha256:4d93e034ce6cd5ed51447f399bc76b0d9b45fcb47dd0175ee928a3848ab35109' and plan['wheel_sha256']=='263b924576d9519c43d5a1acff50a03ab03209d16d26c53543c9ab9a409fb93f','runtime carrier')
 rea=parsed((p/'rea-identity.json').read_text());need(rea['sha256']==plan['wheel_sha256'] and rea['closed'] is True and rea['format']=='zip','REA carrier identity')
 validation=parsed((p/'runtime-validation.json').read_text());need(validation['before'] is True and validation['after'] is True and validation['wheel_sha256']==plan['wheel_sha256'] and validation['validator_sha256']==plan['runtime_validator_sha256'],'runtime file validation')
 run=parsed((p/'execution.json').read_text());need(integer(run['exit'],0) and run['timeout'] is False and integer(run['executions'],1) and run['retry'] is False and run['stderr']=='' and run['command']==docker_command(plan),'execution/command')
 cleanup=parsed((p/'container-cleanup.json').read_text());need(cleanup['owned_name']==plan['name'] and cleanup['owner_label']==plan['owner'] and integer(cleanup['remaining_exit'],0) and cleanup['remaining']=='' and (cleanup['cleanup_exit'] is None or integer(cleanup['cleanup_exit'],0)),'cleanup')
 if integer(cleanup['inspect_exit'],0):need(cleanup['inspect_owner']==plan['owner'],'ownership')
 inventory=parsed((p/'existing-containers.json').read_text());need(inventory['existing_preserved'] is True and set(inventory['before'])<=set(inventory['after']),'user containers')
 start=parsed((p/'started.json').read_text());deadline=datetime.datetime(2026,10,19,17,20,tzinfo=datetime.timezone.utc)
 need(start['deadline_utc']==run['deadline_utc']=='2026-10-19T17:20:00Z' and datetime.datetime.fromisoformat(start['at'])<datetime.datetime.fromisoformat(run['fixture_completed_at'])<=datetime.datetime.fromisoformat(cleanup['completed_at'])<=datetime.datetime.fromisoformat(run['completed_at'])<deadline,'deadline/cleanup chronology')
 v=parsed((p/'owned-output/result.json').read_text());result=rows_observed(p,v)
 need(H((NODE/'seal.json').read_bytes())==NODE_SEAL,'Node seal')
 for n,h in parsed((NODE/'seal.json').read_text())['files'].items():
  q=NODE/n;need(not q.is_symlink() and q.resolve().is_relative_to(NODE.resolve()) and H(q.read_bytes())==h,'Node member')
 for name in NAMES:
  prior='js-failed-grow' if name=='host-failed-grow' else name;need((p/'owned-output'/(name+'.raw')).read_bytes()==(NODE/'owned-output'/(prior+'.raw')).read_bytes(),'complete producer relation')
 result.update(producer_relation_bytes=524288,owned_cleanup_verified=True,existing_containers_preserved=True,runtime=v['wasmtime'],host=v['host_system'],architecture=v['architecture'])
 return result
if __name__=='__main__':print(json.dumps(observed(Path(__file__).resolve().parent),sort_keys=True))
