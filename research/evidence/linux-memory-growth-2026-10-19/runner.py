"""Offline Linux Wasmtime core memory assay; no JavaScript host-view claims."""
from pathlib import Path
import hashlib,importlib.metadata,json,platform,signal
import wasmtime
signal.alarm(20)
root=Path('/experiment');out=Path('/out')
need=lambda v,s:None if v else (_ for _ in ()).throw(ValueError(s))
need(platform.system()=='Linux' and platform.machine()=='aarch64','Linux ARM64')
raw=(root/'probe.wasm').read_bytes();sha=hashlib.sha256(raw).hexdigest();need(sha=='970468fb9b02b07bd628c530877571db3d2ca614f73e8498b6fdd40455b3c0c6','module identity')
config=wasmtime.Config();config.consume_fuel=True;engine=wasmtime.Engine(config);module=wasmtime.Module(engine,raw)
need(not list(module.imports),'import free')
store=wasmtime.Store(engine);store.set_limits(memory_size=196608,instances=1,memories=1);store.set_fuel(100000)
exports=wasmtime.Instance(store,module,[]).exports(store);memory=exports['memory'];store8=exports['store8'];grow=exports['grow']
need(memory.size(store)==1 and memory.type(store).limits.min==1 and memory.type(store).limits.max==2,'module limits')
initial=bytearray(b'\xa5'*65536)
for y in range(5):
 for x in range(17):
  for c in range(4):initial[y*96+x*4+c]=(x*7+y*11+c*31)&255
memory.write(store,initial,0);store8(store,0,17)
rows=[];events=[]
def save(stage):
 data=bytes(memory.read(store,0,memory.data_len(store)));name=stage+'.raw'
 with (out/name).open('xb') as f:f.write(data)
 rows.append({'stage':stage,'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
save('initial')
value=memory.grow(store,0);events.append({'phase':'zero-grow','return_value':value,'pages':memory.size(store)});store8(store,1,34);save('zero-grow')
store.set_fuel(100000);value=grow(store,1);events.append({'phase':'positive-grow','return_value':value,'pages':memory.size(store)});store8(store,65539,51);save('positive-grow')
error=None
try:memory.grow(store,1)
except wasmtime.WasmtimeError as e:error=type(e).__name__
events.append({'phase':'host-failed-grow','error':error,'pages':memory.size(store)});store8(store,2,68);save('host-failed-grow')
store.set_fuel(100000);value=grow(store,1);events.append({'phase':'wasm-failed-grow','return_value':value,'pages':memory.size(store)});store8(store,3,85);save('wasm-failed-grow')
result={'pid':__import__('os').getpid(),'host_system':platform.system(),'architecture':platform.machine(),'kernel':platform.release(),'python':platform.python_version(),'wasmtime':importlib.metadata.version('wasmtime'),'module_sha256':sha,'module_bytes':len(raw),'imports':0,'module_min_pages':1,'module_max_pages':2,'store_memory_limit_bytes':196608,'fuel_per_call':100000,'rows':rows,'events':events,'fresh_copy_reads':True,'js_host_view_semantics_measured':False,'browser_verified':False,'canvas_qualified':False,'product_integration':False}
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'completed','snapshot_count':len(rows)}))
