// Original CLI execution with only explicit standard-I/O handles, no preopens.
const fs = require('node:fs');
const { WASI } = require('node:wasi');
(async () => {
  const [wasm, input, output, mode] = process.argv.slice(2);
  const inFd = fs.openSync(input, 'r'), outFd = fs.openSync(output, 'w');
  try {
    const wasi = new WASI({version:'preview1', args:['inspect-service-message', ...(mode === 'canonical' ? ['--canonical'] : []), '-'], env:{}, preopens:{}, stdin:inFd, stdout:outFd, returnOnExit:true});
    const module = await WebAssembly.compile(fs.readFileSync(wasm));
    const instance = await WebAssembly.instantiate(module, wasi.getImportObject());
    const status = wasi.start(instance);
    if (status !== 0) throw new Error(`WASI exit ${status}`);
  } finally {fs.closeSync(inFd); fs.closeSync(outFd);}
})().catch(error => {console.error(error); process.exitCode = 1;});
