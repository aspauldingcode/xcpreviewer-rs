"""Offline actual Linux execution of pinned source-derived modules and checkers."""
import hashlib
import importlib.metadata
import json
import pathlib
import platform
import wasmtime


def main():
    root=pathlib.Path('/evidence');out=pathlib.Path('/out')
    if platform.system()!='Linux' or platform.machine()!='aarch64':raise ValueError('Actual Linux ARM64 required')
    jobs=json.loads((root/'jobs.json').read_text());checkers=json.loads((root/'wasmkit.json').read_text())
    config=wasmtime.Config();config.consume_fuel=True;engine=wasmtime.Engine(config)
    def module(path,sha):
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Source module hash mismatch')
        m=wasmtime.Module(engine,raw)
        if list(m.imports):raise ValueError('Host imports forbidden')
        return m
    def instance(m):
        store=wasmtime.Store(engine);store.set_limits(memory_size=131072,instances=1,memories=1);store.set_fuel(10000000)
        return store,wasmtime.Instance(store,m,[]).exports(store)
    frames=[];invalid=[];controls=[];aggregates=[];checker_invalid=[]
    for job,checker in zip(jobs,checkers):
        i=job['index'];m=module(root/('source-%d.wasm'%i),job['module_sha256'])
        for s,stride in enumerate(job['strides']):
            for repeat in range(2):
                store,e=instance(m);ptr=e['pixels'](store);cap=e['capacity'](store)
                if cap!=16384:raise ValueError('Source capacity changed')
                memory=e['memory'];memory.write(store,b'\xc3'*cap,ptr)
                if e['render'](store,stride)!=stride*job['config']['height']:raise ValueError('Source length mismatch')
                raw=bytes(memory.read(store,ptr,ptr+cap))
                if raw!=(root/('expected-%d-%d.raw'%(i,s))).read_bytes():raise ValueError('Linux source bytes mismatch')
                (out/('frame-%d-%d-%d.raw'%(i,s,repeat))).write_bytes(raw)
                frames.append({'job':i,'stride_index':s,'repeat':repeat,'bytes':cap,'sha256':hashlib.sha256(raw).hexdigest()})
        store,e=instance(m);ptr=e['pixels'](store);memory=e['memory'];memory.write(store,b'\xc3'*16384,ptr)
        if e['render'](store,job['strides'][0])!=job['strides'][0]*job['config']['height']:raise ValueError('Invalid baseline rejected')
        before=bytes(memory.read(store,ptr,ptr+16384))
        for k,stride in enumerate((0,job['config']['width']*4-1,257,-1)):
            store.set_fuel(10000000)
            if e['render'](store,stride)!=0:raise ValueError('Invalid source stride accepted')
            raw=bytes(memory.read(store,ptr,ptr+16384))
            if raw!=before:raise ValueError('Invalid source stride writes')
            (out/('invalid-%d-%d.raw'%(i,k))).write_bytes(raw)
            invalid.append({'job':i,'index':k,'stride':stride & 0xffffffff})
        cm=module(root/('checker-%d.wasm'%i),checker['module_sha256']);store,e=instance(cm)
        for s in range(2):
            for mutation in range(5):
                store.set_fuel(10000000);count=e['verify'](store,s,mutation)&0xffffffff
                if count!=(1 if mutation else 0):raise ValueError('Source checker disagreement')
                controls.append({'job':i,'stride_index':s,'mutation':mutation,'count':count})
        store.set_fuel(10000000);count=e['verify_all'](store)&0xffffffff
        if count!=8:raise ValueError('Source aggregate checker disagreement')
        aggregates.append({'job':i,'count':count,'module_sha256':checker['module_sha256']})
        store.set_fuel(10000000)
        if e['verify'](store,0,0)!=0:raise ValueError('Checker negative baseline mismatch')
        memory=e['memory'];cap=memory.data_len(store)
        if cap!=131072:raise ValueError('Checker memory bounds changed')
        baseline=bytes(memory.read(store,0,cap))
        (out/('checker-baseline-%d.raw'%i)).write_bytes(baseline)
        for k,(s,mutation) in enumerate(((2,0),(0,5),(-1,0),(0,-1))):
            store.set_fuel(10000000);count=e['verify'](store,s,mutation)&0xffffffff
            raw=bytes(memory.read(store,0,cap))
            if count!=0xffffffff or raw!=baseline:raise ValueError('Invalid checker call accepted or writes')
            (out/('checker-invalid-%d-%d.raw'%(i,k))).write_bytes(raw)
            checker_invalid.append({'job':i,'index':k,'stride_index':s & 0xffffffff,'mutation':mutation & 0xffffffff,'count':count,'baseline_sha256':hashlib.sha256(baseline).hexdigest(),'bytes':cap})
    result={'host_system':platform.system(),'architecture':platform.machine(),'kernel':platform.release(),'python':platform.python_version(),'wasmtime':importlib.metadata.version('wasmtime'),'frames':frames,'invalid':invalid,'checker_invalid':checker_invalid,'controls':controls,'aggregates':aggregates,'imports':0,'fuel_per_call':10000000,'memory_limit_bytes':131072,'renderer_hashes':[j['module_sha256'] for j in jobs]}
    (out/'linux-source.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
