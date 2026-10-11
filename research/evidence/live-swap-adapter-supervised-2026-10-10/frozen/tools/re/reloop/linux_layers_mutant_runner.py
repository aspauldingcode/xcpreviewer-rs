"""Actual offline Linux semantic mutants against embedded frozen native targets."""
import hashlib
import importlib.metadata
import json
import pathlib
import platform
import wasmtime


def main():
    root=pathlib.Path('/evidence');out=pathlib.Path('/out')
    if platform.system()!='Linux' or platform.machine()!='aarch64':raise ValueError('Linux ARM64 required')
    config=wasmtime.Config();config.consume_fuel=True;engine=wasmtime.Engine(config);rows=[]
    for item in json.loads((root/'mutations.json').read_text()):
        name=item['mutation'];raw=(root/(name+'.wasm')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item['module_sha256']:raise ValueError('Semantic mutant identity changed')
        module=wasmtime.Module(engine,raw)
        if list(module.imports):raise ValueError('Mutant imports forbidden')
        store=wasmtime.Store(engine);store.set_limits(memory_size=131072,instances=1,memories=1);store.set_fuel(10000000)
        e=wasmtime.Instance(store,module,[]).exports(store);controls=[]
        for variant in range(40):
            store.set_fuel(10000000);controls.append({'variant':variant,'mismatches':e['verify'](store,variant,0)&0xffffffff})
        expected=json.loads((root/(name+'.json')).read_text())
        if controls!=expected['rows']:raise ValueError('Linux semantic mutant count differs from anchored V8')
        store.set_fuel(50000000);aggregate=e['verify_all'](store,0)&0xffffffff
        if aggregate!=0xffffffff:raise ValueError('Algorithm mutant passed native aggregate')
        rows.append({'mutation':name,'module_sha256':item['module_sha256'],'rows':controls,'aggregate':aggregate,'witness':controls[8]['mismatches']})
    result={'host_system':platform.system(),'architecture':platform.machine(),'kernel':platform.release(),'python':platform.python_version(),'wasmtime':importlib.metadata.version('wasmtime'),'imports':0,'memory_limit_bytes':131072,'fuel_per_case':10000000,'fuel_per_aggregate':50000000,'mutants':rows}
    (out/'linux-layer-mutants.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
