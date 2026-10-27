// WASI preview1 control with no filesystem preopens or inherited environment.
const fs = require('node:fs');
const { WASI } = require('node:wasi');
(async () => {
  const wasi = new WASI({ version: 'preview1', args: ['reply_pipeline'], env: {}, preopens: {}, returnOnExit: true });
  const module = await WebAssembly.compile(fs.readFileSync(process.argv[2]));
  const instance = await WebAssembly.instantiate(module, wasi.getImportObject());
  const status = wasi.start(instance);
  if (status !== 0) throw new Error(`WASI exit ${status}`);
})().catch(error => { console.error(error); process.exitCode = 1; });
