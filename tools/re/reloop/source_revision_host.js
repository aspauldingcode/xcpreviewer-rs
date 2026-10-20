'use strict';
// Owned source-generation policy. Build and byte oracle remain external adapters.
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const {LiveWasmHost}=require('./live_wasm_host.js');
class SourceRevisionHost {
  #host=new LiveWasmHost(); #latest=null; #generation=0; #closed=false;
  begin(source) {
    assert(!this.#closed,'Source host closed');
    assert(Buffer.isBuffer(source) && source.length>0 && source.length<=4096);
    const snapshot=Buffer.from(source);
    assert(snapshot.every(byte=>byte<128),'ASCII source required');
    assert(this.#generation<Number.MAX_SAFE_INTEGER);
    this.#latest=Object.freeze({generation:++this.#generation,
      sourceSha256:crypto.createHash('sha256').update(snapshot).digest('hex')});
    return this.#latest;
  }
  invalidate(){
    assert(!this.#closed,'Source host closed');
    assert(this.#generation<Number.MAX_SAFE_INTEGER);
    ++this.#generation;this.#latest=null;
  }
  submit(ticket,build,expected,timeout=1500) {
    assert(!this.#closed && ticket===this.#latest,'Stale or foreign build ticket');
    // Builder properties may be accessors. Snapshot the module before later
    // receipt/configuration reads can mutate the caller's buffer or source.
    const sourceSha256=build.sourceSha256;
    const bytes=build.module;
    assert(Buffer.isBuffer(bytes));
    const module=Buffer.from(bytes);
    const moduleSha256=build.moduleSha256,config=build.config;
    const width=config.width,height=config.height,stride=build.stride;
    assert(!this.#closed && ticket===this.#latest,'Stale or foreign build ticket');
    assert.equal(sourceSha256,ticket.sourceSha256,'Build source receipt mismatch');
    assert.equal(crypto.createHash('sha256').update(module).digest('hex'),moduleSha256,
      'Build module receipt mismatch');
    return this.#host.propose(module,expected,width,height,stride,timeout,
      ()=>!this.#closed && ticket===this.#latest,ticket);
  }
  snapshot(){return this.#host.snapshot();}
  verifyLive(){return this.#host.verifyLive();}
  status(){return this.#host.status();}
  async close(){this.#closed=true;await this.#host.close();}
}
module.exports={SourceRevisionHost};
