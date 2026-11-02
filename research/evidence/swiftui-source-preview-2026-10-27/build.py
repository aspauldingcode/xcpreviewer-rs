from pathlib import Path
import subprocess,os
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;b=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin');env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')};env.update(RUSTC=str(b/'rustc'),RUSTDOC=str(b/'rustdoc'))
for n,args in [('host-build',[str(b/'cargo'),'build','--offline','--locked','--manifest-path',str(r/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(w/'target'),'--bin','canvas-frame']),('wasm-build',[str(b/'cargo'),'rustc','--offline','--locked','--manifest-path',str(r/'tools/re/rust/canvas-core/Cargo.toml'),'--target-dir',str(w/'target'),'--target','wasm32-wasip1','--bin','canvas-frame','--','-C','link-arg=--max-memory=268435456'])]:
 p=subprocess.run(args,cwd=r,env=env,capture_output=True,timeout=60);(w/(n+'.stdout')).write_bytes(p.stdout);(w/(n+'.stderr')).write_bytes(p.stderr);p.check_returncode()
