"""Offline Linux-only execution of anchored owned WASM modules."""
import hashlib
import importlib.metadata
import json
import pathlib
import platform
import sys
import wasmtime


def checked(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('Anchored module hash mismatch')
    return raw


def main():
    root = pathlib.Path('/evidence');out = pathlib.Path('/out')
    if platform.system() != 'Linux' or platform.machine() != 'aarch64':
        raise ValueError('Actual Linux ARM64 host required')
    config = wasmtime.Config();config.consume_fuel = True
    engine = wasmtime.Engine(config)
    def instance(raw):
        module = wasmtime.Module(engine, raw)
        if list(module.imports):raise ValueError('No host imports permitted')
        store = wasmtime.Store(engine);store.set_limits(memory_size=1048576, instances=1, memories=1)
        store.set_fuel(100000000)
        return store, wasmtime.Instance(store, module, []).exports(store)
    frames = [];negative = 0
    for job in json.loads((root / 'jobs.json').read_text()):
        index = job['index'];raw = checked(root / ('source-%d.wasm' % index), job['module_sha256'])
        store, exports = instance(raw);ptr = exports['pixels'](store);cap = exports['capacity'](store)
        if cap != 204800:raise ValueError('Standalone buffer capacity changed')
        memory = exports['memory'];memory.write(store, b'\xa5' * cap, ptr)
        length = job['stride'] * job['config']['height']
        store.set_fuel(100000000)
        if exports['render'](store, job['stride']) != length:raise ValueError('Linux renderer length mismatch')
        actual = bytes(memory.read(store, ptr, ptr + cap))
        expected = (root / (('native-%d.rgba' if index < 3 else 'expected-%d.rgba') % index)).read_bytes()
        if len(expected) != length or actual != expected + b'\xa5' * (cap - length):
            raise ValueError('Independent Linux full-allocation byte mismatch')
        (out / ('linux-%d.rgba' % index)).write_bytes(actual[:length])
        for stride in (0, job['config']['width'] * 4 - 1, 1281, 0xffffffff):
            store.set_fuel(100000000)
            if exports['render'](store, stride) != 0 or bytes(memory.read(store, ptr, ptr + cap)) != actual:
                raise ValueError('Linux invalid request mutated allocation')
            negative += 1
        frames.append({'index': index, 'module_sha256': job['module_sha256'], 'output_bytes': length,
                       'output_sha256': hashlib.sha256(actual[:length]).hexdigest(), 'allocation_bytes_compared': cap})
    rows = []
    for item in json.loads((root / 'checker-modules.json').read_text()):
        index = item['index'];raw = checked(root / ('checker-%d/checked.wasm' % index), item['module_sha256'])
        store, exports = instance(raw)
        for function in ('verify', 'verify_rejected'):
            for argument in range(5):
                store.set_fuel(100000000)
                actual = exports[function](store, argument) & 0xffffffff
                expected = 0xffffffff if argument > 3 else int(function == 'verify' and argument != 0)
                if actual != expected:raise ValueError('Linux checker fault/rejection mismatch')
                rows.append({'module': index, 'function': function, 'argument': argument, 'actual': actual, 'expected': expected, 'passed': True})
    result = {'host_system': platform.system(), 'kernel': platform.release(), 'architecture': platform.machine(),
              'python': platform.python_version(), 'wasmtime': importlib.metadata.version('wasmtime'),
              'frames': frames, 'checker_rows': rows, 'negative_requests': negative, 'imports': 0,
              'memory_limit_bytes': 1048576, 'fuel_per_call': 100000000}
    (out / 'linux-execution.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
