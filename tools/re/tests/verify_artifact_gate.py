"""Independent expectations and fresh filesystem replay for bounded artifact reads."""
import hashlib,json,subprocess,shutil,tempfile,sys,importlib.util
from pathlib import Path

def sha(b):return hashlib.sha256(b).hexdigest()
def verify(folder):
    folder=Path(folder);s=importlib.util.spec_from_file_location('pin_reader',Path(__file__).with_name('verify_rust_pin.py'));reader=importlib.util.module_from_spec(s);s.loader.exec_module(reader);reader.verify(folder)
    source=json.loads((folder/'control/live/result.json').read_text());build=source['builds'][0];module=folder/'control/live'/build['stage']/'result/view.wasm';raw=module.read_bytes();d=json.loads((folder/'gate/result.json').read_text());assert d['expectedSha']==sha(raw)==build['receipt']['module_sha256'] and d['expectedBytes']==len(raw)
    modes=['valid','empty','oversize','directory','fifo','symlink-swap','grow','mtime'];assert [x['mode'] for x in d['controls']]==modes
    def check(row,mode):
        count=0 if mode=='symlink-swap' else 1
        assert row['mode']==mode and type(row['opened']) is int and type(row['closed']) is int and row['opened']==row['closed']==count
        assert row['accepted'] is (mode=='valid')
        if mode=='valid':assert row['sha']==sha(raw) and row['bytes']==len(raw) and row['error'] is None
        else:assert row['sha'] is None and row['bytes']==0 and isinstance(row['error'],str) and row['error']
        if mode in ['grow','mtime']:assert row['mutated'] is True
    for row in d['controls']:check(row,row['mode']);assert type(row['elapsedMs']) is int and 0<=row['elapsedMs']<2000
    with tempfile.TemporaryDirectory(prefix='artifact-reader-') as tmp:
        for mode in modes:
            # Recreate real FIFO/path-swap/growth fixtures and use frozen production helper.
            r=subprocess.run([shutil.which('node'),str(folder/'reader/artifact_worker.js'),mode,str(Path(tmp)/mode),str(module.resolve()),str((folder/'reader/bounded_artifact.js').resolve()),sys.executable],capture_output=True,timeout=2)
            assert r.returncode==0 and len(r.stdout)<65536,r.stderr.decode();check(json.loads(r.stdout),mode)
    return {'cases':8,'replayed':8,'module_bytes':len(raw),'review':'pending'}
