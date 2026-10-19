"""Second non-browser engine acquisition, independent arrays and prior producer relation."""
from pathlib import Path
import datetime
import json
from phase_prerequisites import parsed,require as need,receipt,digest,integer
import byte_compare as b
from predictions import NAMES
NODE_SEAL='1d33cf1b2cbe14f364e7647671de91e5581d8583426be701e39ca45c377dcaa6'
NODE=Path('/Users/8amps/xcpreviewer-rs/research/evidence/wasm-memory-growth-2026-10-19')

def anchored_node(root=NODE):
 root=Path(root);need(b.H((root/'seal.json').read_bytes())==NODE_SEAL,'Node seal')
 seal=parsed((root/'seal.json').read_text())
 for n,h in seal['files'].items():
  f=root/n;need(not f.is_symlink() and f.resolve().is_relative_to(root.resolve()) and b.H(f.read_bytes())==h,'Node member')
 need((root/'probe.wasm').read_bytes()==Path(__file__).with_name('probe.wasm').read_bytes(),'same WASM module')
 return root

def rows_observed(p,value):
 result=b.result(p,value)
 need(value['engine']=='public JavaScriptCore JSContext' and value['native_UI_execution'] is False and value['non_Apple_OS_verified'] is False and value['canvas_qualified'] is False,'engine/scope')
 env=value['environment'];framework=parsed((Path(p)/'framework-before.json').read_text())
 need(env['framework_identifier']==framework['identifier']=='com.apple.JavaScriptCore' and env['framework_version']==framework['version'] and env['framework_path']=='/System/Library/Frameworks/JavaScriptCore.framework' and env['machine']=='arm64' and env['system']=='Darwin','public framework identity')
 need(type(value['engine_exports']) is list and len(value['engine_exports'])==3 and [{'name':e['name'],'kind':e['kind']} for e in value['engine_exports']]==value['exports'],'descriptor projection')
 node=anchored_node()
 for name in NAMES:need((Path(p)/'owned-documents'/(name+'.raw')).read_bytes()==(node/'owned-output'/(name+'.raw')).read_bytes(),'complete producer relation')
 result.update(second_engine_verified=True,engine='public JavaScriptCore JSContext',environment=env,producer_relation_bytes=524288,engine_descriptor_type_semantics_qualified=False)
 return result

def observed(root):
 p=Path(root)
 for n,h in parsed((p/'approved-pins.json').read_text()).items():need(digest(p/n)==h,'approved pin')
 source=digest(p/'probe.c');binary=parsed((p/'compile-record.json').read_text())['binary_sha256']
 need(type(binary) is str and len(binary)==64 and all(c in '0123456789abcdef' for c in binary),'binary hash')
 records={phase:receipt(p,phase,source,binary) for phase in ['compile','output-valid','fixture']}
 execution='/private/tmp/jsc-memory-growth-20261019'
 need(records['compile']['command']=='/usr/bin/xcrun' and records['compile']['args']==['clang','-x','objective-c','-fobjc-arc','-framework','Foundation','-framework','JavaScriptCore',execution+'/probe.c','-o',execution+'/probe'],'compile command')
 need(records['fixture']['command']==execution+'/probe' and records['fixture']['args']==['--fixture',execution+'/owned-documents'] and records['output-valid']['command']==execution+'/probe','execution commands')
 rea=parsed((p/'rea-identity.json').read_text());need(rea['owned_binary_sha256']==binary and rea['closed'] is True and rea['architecture']=='arm64','REA binding')
 times=[];deadline=datetime.datetime(2026,10,19,17,10,tzinfo=datetime.timezone.utc)
 for phase in ['compile','output-valid','fixture']:
  v=parsed((p/(phase+'-started.json')).read_text());t=datetime.datetime.fromisoformat(v['started_at']);need(v['phase']==phase and v['deadline_utc']=='2026-10-19T17:10:00Z' and t<deadline,'phase chronology');times.append(t)
 env=parsed((p/'environment-before.json').read_text());need(datetime.datetime.fromisoformat(env['observed_at'])<times[0] and env['timing']=='before acquisition','host chronology')
 complete=parsed((p/'completed.json').read_text());end=datetime.datetime.fromisoformat(complete['completed_at']);need(complete['deadline_utc']=='2026-10-19T17:10:00Z' and times==sorted(times) and times[-1]<end<deadline,'completion chronology')
 record=records['fixture']['record'];value=parsed(record['stdout']);need(integer(value['pid']) and record['stderr']=='owned_tree_pid:'+str(value['pid'])+'\n','owned streams')
 return rows_observed(p,value)
if __name__=='__main__':print(json.dumps(observed(Path(__file__).resolve().parent),sort_keys=True))
