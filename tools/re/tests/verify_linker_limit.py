"""Independently verify retained failed-control artifacts without upgrading missing receipts."""
import hashlib,json,subprocess,shutil,importlib.util,re
from pathlib import Path
from reloop.primarysource import parse,expected

def sha(b):return hashlib.sha256(b).hexdigest()
def verify(folder):
    folder=Path(folder);m=json.loads((folder/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}
    for name,row in m['files'].items():
        p=folder/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts and not p.is_symlink();b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
    provenance=json.loads((folder/'provenance.json').read_text());assert provenance['attempt_reports_missing'] is True and provenance['supervisor_poll_seconds']==0.025
    s=importlib.util.spec_from_file_location('pin_reader',Path(__file__).with_name('verify_rust_pin.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader);jobs=[]
    for n in range(2):
        root=folder/'attempts'/str(n);reader.verify(root);run=json.loads((root/'run.json').read_text());assert run['valid'] is False and run['receipts_missing'] is True
        cfg=json.loads((root/'linker/config.json').read_text());tc=json.loads((root/'control/toolchain.json').read_text());assert cfg['toolchainPin']==tc['sha256'] and cfg['linkerSha']==tc['identity']['linkers']['rust-lld']['sha256']
        assert sha((root/'linker/contract.rs').read_bytes())==sha((root/'frozen/contract.rs').read_bytes())
        first=json.loads((root/'control/live/result.json').read_text())['builds'][0];original=(root/'control/live'/first['stage']/'result/module.rs').read_text();normalize=lambda text:re.sub(r'#\[path = "[^"]+"\]','#[path = "OWNED_CONTRACT"]',text)
        kernel=(root/'linker/kernel.rs').read_text();assert normalize(kernel)==normalize(original)
        stress=kernel+''.join('\n#[no_mangle] pub extern "C" fn stress_'+str(i)+'()->u32 {'+str(i)+'}\n' for i in range(6000));assert (root/'linker/abort.rs').read_text()==stress
        oracle=expected(parse((root/'fixture/0-source.swift').read_text()),64);assert (root/'linker/baseline.raw').read_bytes()==oracle
        stderr=(root/'linker/control.stderr').read_text()
        if n==0:assert 'actual: 0' in stderr and 'notStrictEqual' in stderr and 'assert.notEqual(execution.report.target_code,0)' in (root/'linker/rust_linker_control.js').read_text()
        else:assert 'Actual live pinned rust-lld identity must be observed' in stderr and 'actual: null' in stderr
        assert 'time.sleep(.025)' in (root/'linker/observed_group_anchor.py').read_text();jobs.append({'module':str(root/'linker/abort.wasm'),'expected':str(root/'fixture/0-expected.raw'),'height':cfg['config']['height']})
    script="const fs=require('fs'),a=require('assert/strict');for(const r of JSON.parse(process.argv[1])){const m=new WebAssembly.Module(fs.readFileSync(r.module));a.equal(WebAssembly.Module.imports(m).length,0);const names=WebAssembly.Module.exports(m).map(x=>x.name).sort(),want=['memory','capacity','pixels','render',...Array.from({length:6000},(_,i)=>'stress_'+i)].sort();a.deepEqual(names,want);const e=new WebAssembly.Instance(m).exports;for(let i=0;i<6000;i++)a.equal(e['stress_'+i](),i);a.equal(e.capacity(),16384);a.equal(e.memory.buffer.byteLength,131072);const p=e.pixels();a(p>=0&&p+16384<=131072);a.equal(e.render(64),r.height*64);a.deepEqual(Buffer.from(new Uint8Array(e.memory.buffer,p,16384)),fs.readFileSync(r.expected));}"
    r=subprocess.run([shutil.which('node'),'-e',script,json.dumps(jobs)],capture_output=True,timeout=10);assert r.returncode==0,r.stderr.decode();return {'retained_attempts':2,'bytes':32768,'stress_exports_checked':12000,'native_acceptance':False}
