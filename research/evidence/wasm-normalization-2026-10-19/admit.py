"""Independent research arithmetic admission, not WASM Canvas delivery."""
from pathlib import Path
import json,hashlib,datetime
from predictions import readback
from build import module
BASE=Path('/Users/8amps/xcpreviewer-rs/research/evidence/quartz-byte-normalization-2026-10-19')
METHODS=['wasm-multiply','wasm-divide','js-multiply','js-divide']
def need(v):
 if not v:raise ValueError('Arithmetic conformance rejected')
def parsed(raw):
 def pairs(items):
  d={}
  for k,v in items:need(k not in d);d[k]=v
  return d
 def constant(v):raise ValueError('Nonfinite JSON')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
def admit(root):
 p=Path(root);need(hashlib.sha256((BASE/'seal.json').read_bytes()).hexdigest()=='3ee732a9464d3ed82174448e8019b00c4fa436b6114feb920569f346a3d5b538')
 for n,h in parsed((BASE/'seal.json').read_text())['files'].items():need(hashlib.sha256((BASE/n).read_bytes()).hexdigest()==h)
 outer=parsed((p/'execution.json').read_text());need(type(outer['exit']) is int and outer['exit']==0 and outer['stderr']=='' and type(outer['executions']) is int and outer['executions']==1)
 need(outer['deadline_utc']=='2026-10-19T09:35:00Z' and datetime.datetime.fromisoformat(outer['completed_at'])<datetime.datetime(2026,10,19,9,35,tzinfo=datetime.timezone.utc))
 out=parsed(outer['stdout']);need(type(out['pid']) is int and 1<out['pid']<2**31 and all(type(out['environment'][k]) is str and out['environment'][k] for k in ['node','v8','platform','arch']))
 raw=(p/'probe.wasm').read_bytes();need(raw==module() and out['module_sha256']==hashlib.sha256(raw).hexdigest() and type(out['module_bytes']) is int and out['module_bytes']==81 and type(out['sections']) is list and all(type(x) is int for x in out['sections']) and out['sections']==[1,3,7,10] and out['imports']==[])
 need(out['exports']==[{'name':'multiplyBits','kind':'function'},{'name':'divideBits','kind':'function'}] and type(out['scalar_dispatches']) is int and out['scalar_dispatches']==9216)
 need([x['label'] for x in out['invalid_inputs']]==['negative','large','fraction','nonfinite','boolean'] and all(x['rejected'] is True and type(x['dispatch_delta']) is int and x['dispatch_delta']==0 for x in out['invalid_inputs']))
 need(all(out[k] is False for k in ['native_UI_execution','product_integration','second_runtime_verified','non_Apple_OS_verified']))
 rows=out['rows'];need(type(rows) is list and [x['method'] for x in rows]==METHODS);expected_names=set();results=[]
 for row in rows:
  method=row['method'];candidate='multiply' if method.endswith('multiply') else 'divide';name=method+'.raw';expected_names.add(name);q=p/'owned-output'/name;need(row['file']==name and not q.is_symlink());actual=q.read_bytes();expected=readback(candidate)
  native=(BASE/'owned-documents'/('route0-readback.raw' if candidate=='multiply' else 'route1-readback.raw')).read_bytes();need(type(row['allocation_bytes']) is int and row['allocation_bytes']==16384 and actual==expected==native and hashlib.sha256(actual).hexdigest()==row['sha256'])
  wrong=(BASE/'owned-documents'/('route1-readback.raw' if candidate=='multiply' else 'route0-readback.raw')).read_bytes();diff=sum(a!=b for a,b in zip(actual,wrong));need(diff==1152);results.append({'method':method,'native_route':0 if candidate=='multiply' else 1,'exact':True,'opposite_expression_mismatch_bytes':diff})
 need({x.name for x in (p/'owned-output').iterdir()}==expected_names)
 return {'scalar_arithmetic_conformance':True,'full_bytes_compared':65536,'padding_bytes':768,'tail_bytes':15616,'invalid_domain_rejections':5,'module_bytes':81,'results':results,'single_Node_V8_host_only':True,'product_integration':False,'second_runtime_verified':False,'non_Apple_OS_verified':False,'canvas_qualified':False}
if __name__=='__main__':print(json.dumps(admit(Path(__file__).resolve().parent)))
