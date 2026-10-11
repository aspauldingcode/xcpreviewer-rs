"""Actual offline Linux layer execution; expectations supplied by pinned native/model files."""
import hashlib
import importlib.metadata
import json
import pathlib
import platform
import wasmtime


def checked(path,sha):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Anchored layer module hash mismatch')
    return raw


def main():
    root=pathlib.Path('/evidence');out=pathlib.Path('/out')
    if platform.system()!='Linux' or platform.machine()!='aarch64':raise ValueError('Actual Linux ARM64 required')
    identities=json.loads((root/'identities.json').read_text())
    config=wasmtime.Config();config.consume_fuel=True;engine=wasmtime.Engine(config)
    module=wasmtime.Module(engine,checked(root/'layers.wasm',identities['renderer_module']))
    checker=wasmtime.Module(engine,checked(root/'layers-checker.wasm',identities['checker_module']))
    if list(module.imports) or list(checker.imports):raise ValueError('No layer host imports permitted')
    def instance(module):
        store=wasmtime.Store(engine);store.set_limits(memory_size=131072,instances=1,memories=1);store.set_fuel(10000000)
        return store,wasmtime.Instance(store,module,[]).exports(store)
    rows=[]
    for job in json.loads((root/'execution.json').read_text())['rows']:
        index=job['index'];store,e=instance(module);ptr=e['pixels'](store);cap=e['capacity'](store)
        if cap!=16384:raise ValueError('Alpha capacity changed')
        memory=e['memory'];memory.write(store,b'\xc3'*cap,ptr)
        count=e['render'](store,job['w'],job['h'],job['stride'],*json.loads((root/'inputs.json').read_text())[job['variant']],job['reverse'])
        raw=bytes(memory.read(store,ptr,ptr+cap));expected=(root/('expected-%d.raw'%index)).read_bytes()
        if count!=job['stride']*job['h'] or raw!=expected:raise ValueError('Independent Linux layer allocation mismatch')
        (out/('frame-%d.raw'%index)).write_bytes(raw);rows.append({'index':index,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':cap})
    store,e=instance(module);ptr=e['pixels'](store);cap=e['capacity'](store);memory=e['memory'];memory.write(store,b'\xc3'*cap,ptr)
    if e['render'](store,17,9,80,4,2,8,0)!=720:raise ValueError('Invalid control baseline rejected')
    baseline=bytes(memory.read(store,ptr,ptr+cap))
    if baseline!=(root/'invalid-expected.raw').read_bytes():raise ValueError('Invalid baseline mismatch')
    negatives=json.loads((root/'execution.json').read_text())['invalid']
    for index,args in enumerate(negatives):
        store.set_fuel(10000000)
        if e['render'](store,*args)!=0:raise ValueError('Linux invalid layer request accepted')
        raw=bytes(memory.read(store,ptr,ptr+cap))
        if raw!=baseline:raise ValueError('Invalid layer request mutated memory')
        (out/('invalid-%d.raw'%index)).write_bytes(raw)
    controls=[];store,e=instance(checker)
    for variant in range(40):
        for mutation in range(5):
            store.set_fuel(10000000);count=e['verify'](store,variant,mutation)&0xffffffff
            if count!=(1 if mutation else 0):raise ValueError('Native layer checker disagreement')
            controls.append({'variant':variant,'mutation':mutation,'count':count})
    result={'host_system':platform.system(),'architecture':platform.machine(),'kernel':platform.release(),'python':platform.python_version(),'wasmtime':importlib.metadata.version('wasmtime'),'frames':rows,'invalid_requests':len(negatives),'checker_rows':controls,'imports':0,'fuel_per_call':10000000,'memory_limit_bytes':131072,'renderer_module_sha256':identities['renderer_module'],'checker_module_sha256':identities['checker_module']}
    (out/'linux-layers.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
