"""Independent actual compiler wait/drain, frame-retention and recovery reader."""
import json,hashlib,shutil,subprocess
from pathlib import Path
from reloop.primarysource import parse,expected

def sha(b):return hashlib.sha256(b).hexdigest()
def verify(folder):
    folder=Path(folder);m=json.loads((folder/'manifest.json').read_text())
    assert set(m['files'])=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p!=folder/'manifest.json'}
    for name,row in m['files'].items():
        p=folder/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts and not p.is_symlink();b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
    config=json.loads((folder/'control/config.json').read_text());d=json.loads((folder/'control/controls/result.json').read_text());facts=json.loads((folder/'control/result.json').read_text())
    assert facts['prior_anchor']=='7cf8a0b11b90f5f479e8409ba909a160ab77c738a88804b9ab5724ac0a631382'
    raw=(folder/'fixture/prior-manifest.json').read_bytes();assert sha(raw)==facts['prior_anchor'];prior=json.loads(raw)['files']
    for name,key in [('source.swift','fixture/0-source.swift'),('expected.raw','fixture/0-expected.raw')]:
        b=(folder/'fixture'/name).read_bytes();assert len(b)==prior[key]['bytes'] and sha(b)==prior[key]['sha256']
    oracle=expected(parse((folder/'fixture/source.swift').read_text()),64);assert len(oracle)==16384 and oracle==(folder/'fixture/expected.raw').read_bytes()
    assert (folder/'control/controls/baseline.raw').read_bytes()==oracle
    assert [r['mode'] for r in d['controls']]==['abort','deadline','stale']
    for row in d['controls']:
        observed=row['observed'];assert observed['identity'][2]==config['rustc'] and observed['pid']>0 and len(observed['identity'])==3
        execution=row['execution'];report=execution['report'];assert report['drained'] is True and report['remaining_observed']==0 and execution['emergencyClosed'] is False and execution['signal']=='SIGKILL'
        if row['mode']=='stale':assert report['target_code']==0 and report['failure'] is None and 'Stale or foreign' in row['error']
        else:assert report['target_code']<0 and report['failure']==row['mode'] and row['error']
        artifact=folder/'control/controls'/(row['mode']+'.wasm');assert artifact.exists()==row['artifactPresent']
        if artifact.exists():assert sha(artifact.read_bytes())==row['artifactSha']
        else:assert row['artifactSha'] is None
        assert row['retainedRevision']==1 and row['retainedSha']==sha(oracle) and row['lateArtifactStable'] is True
        assert (folder/'control/controls'/(row['mode']+'-retained.raw')).read_bytes()==oracle
    assert d['recovery']['revision']==2 and d['recovery']['execution']['report']['target_code']==0 and d['recovery']['execution']['report']['drained'] is True
    assert d['finalStatus']['liveWorkers']==0 and (folder/'control/controls/recovery.raw').read_bytes()==oracle
    module=folder/'control/controls/recovery.wasm';assert sha(module.read_bytes())==d['recovery']['moduleSha']
    script="const f=require('fs'),a=require('assert/strict'),m=new WebAssembly.Module(f.readFileSync(process.argv[1]));a.equal(WebAssembly.Module.imports(m).length,0);a.deepEqual(WebAssembly.Module.exports(m).map(x=>[x.name,x.kind]).sort(),[['capacity','function'],['memory','memory'],['pixels','function'],['render','function']]);const e=new WebAssembly.Instance(m).exports;a.equal(e.capacity(),16384);a.equal(e.memory.buffer.byteLength,131072);a.equal(e.render(64),448);a.deepEqual(Buffer.from(new Uint8Array(e.memory.buffer,e.pixels(),16384)),f.readFileSync(process.argv[2]));"
    r=subprocess.run([shutil.which('node'),'-e',script,str(module),str(folder/'fixture/expected.raw')],capture_output=True,timeout=10);assert r.returncode==0,r.stderr.decode()
    return {'controls':3,'retained_bytes':49152,'recovery_revision':2,'review':'pending'}
