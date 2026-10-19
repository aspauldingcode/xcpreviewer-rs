"""Fail-closed research conformance reader; no engine execution."""
from pathlib import Path
import json,hashlib,datetime,re
from phase_prerequisites import parsed,require as need,receipt,integer
from predictions import readback
BASE=Path('/Users/8amps/xcpreviewer-rs/research/evidence')
METHODS=['wasm-multiply','wasm-divide','js-multiply','js-divide']
def check_output(out,root):
 p=Path(root)
 need(out['engine']=='public JavaScriptCore JSContext','engine')
 need(integer(out['pid']) and 1<out['pid']<2**31,'pid')
 env=out['environment'];need(all(type(env[k]) is str and env[k] for k in ['framework_path','framework_identifier','framework_version','system','release','machine','os_version']),'environment')
 need(env['framework_identifier']=='com.apple.JavaScriptCore' and env['system']=='Darwin' and env['machine']=='arm64','framework/host')
 need(all(out[k] is False for k in ['native_UI_execution','product_integration','non_Apple_OS_verified','canvas_qualified']),'scope')
 if out['status']=='unsupported':
  need('webassembly_type' in out and type(out['webassembly_type']) is str and out['webassembly_type']!='object' and out['rows']==[] and integer(out['scalar_dispatches'],0),'unsupported')
  need(list((p/'owned-documents').iterdir())==[],'unsupported bytes')
  return {'status':'unsupported','second_engine_scalar_conformance':False,'full_bytes_compared':0}
 need(out['status']=='supported','status')
 need(integer(out['module_bytes'],81) and type(out['sections']) is list and all(integer(x) for x in out['sections']) and out['sections']==[1,3,7,10] and out['imports']==[],'module')
 need(type(out['metadata_json_order_matches']) is bool and type(out['export_key_order']) is list and len(out['export_key_order'])==2 and all(type(k) is list and sorted(k)==['kind','name'] for k in out['export_key_order']) and out['metadata_json_order_matches']==(out['export_key_order']==[['name','kind'],['name','kind']]) and all(set(x)=={'name','kind'} and all(type(v) is str for v in x.values()) for x in out['exports']),'descriptor key provenance')
 need(out['exports']==[{'name':'multiplyBits','kind':'function'},{'name':'divideBits','kind':'function'}] and integer(out['scalar_dispatches'],9216),'dispatch/exports')
 need([x['label'] for x in out['invalid_inputs']]==['negative','large','fraction','nonfinite','boolean'] and all(x['rejected'] is True and integer(x['dispatch_delta'],0) for x in out['invalid_inputs']),'domain')
 need(type(out['rows']) is list and [x['method'] for x in out['rows']]==METHODS,'rows')
 for row in out['rows']:
  m=row['method'];name=m+'.raw';need(row['file']==name and integer(row['allocation_bytes'],16384),'layout')
  q=p/'owned-documents'/name;need(q.is_file() and not q.is_symlink(),'file');actual=q.read_bytes();candidate=m.rsplit('-',1)[1]
  need(actual==readback(candidate),'all predicted bytes')
  native=BASE/'quartz-byte-normalization-2026-10-19'/'owned-documents'/('route0-readback.raw' if candidate=='multiply' else 'route1-readback.raw')
  v8=BASE/'wasm-normalization-2026-10-19'/'owned-output'/name
  need(actual==native.read_bytes()==v8.read_bytes(),'native and V8 comparison')
 need({x.name for x in (p/'owned-documents').iterdir()}=={x+'.raw' for x in METHODS},'inventory')
 return {'status':'supported','second_engine_scalar_conformance':True,'full_bytes_compared':65536,'padding_bytes':768,'tail_bytes':15616,'non_Apple_OS_verified':False,'canvas_qualified':False}
def admit(root):
 p=Path(root)
 for n,h in [('quartz-byte-normalization-2026-10-19','3ee732a9464d3ed82174448e8019b00c4fa436b6114feb920569f346a3d5b538'),('wasm-normalization-2026-10-19','386dae665e14bf98b24486390b56a60e74a0b449b66b5f8dbd0ab598d858697c')]:
  a=BASE/n;need(hashlib.sha256((a/'seal.json').read_bytes()).hexdigest()==h,'anchor seal')
  for f,d in parsed((a/'seal.json').read_text())['files'].items():need(hashlib.sha256((a/f).read_bytes()).hexdigest()==d,'anchor bytes')
 for n,h in parsed((p/'approved-pins.json').read_text()).items():need(hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'approved pin')
 raw=(p/'probe.wasm').read_bytes();need(hashlib.sha256(raw).hexdigest()=='460ce52e8cfb8034e424a87c1e0647441769833137c4d39f4ad8ffc103b90d43','module provenance')
 need('const raw=new Uint8Array('+str(list(raw))+');' in (p/'probe.js').read_text(),'embedded module')
 c=parsed((p/'compile-record.json').read_text());source=hashlib.sha256((p/'probe.c').read_bytes()).hexdigest();binary=c['binary_sha256']
 for phase in ['compile','output-valid','fixture']:receipt(p,phase,source,binary)
 rea=parsed((p/'rea-identity.json').read_text());need(rea['owned_binary_sha256']==binary and rea['architecture']=='arm64' and rea['closed'] is True,'REA binding')
 timing=parsed((p/'completed.json').read_text());need(timing['deadline_utc']=='2026-10-19T09:45:00Z' and datetime.datetime.fromisoformat(timing['completed_at'])<datetime.datetime(2026,10,19,9,45,tzinfo=datetime.timezone.utc),'deadline')
 row=parsed((p/'fixture-record.json').read_text());out=parsed(row['record']['stdout']);need(row['record']['stderr']=='owned_tree_pid:'+str(out['pid'])+'\n','fixture pid/diagnostics')
 return check_output(out,p)
if __name__=='__main__':print(json.dumps(admit(Path(__file__).resolve().parent)))
