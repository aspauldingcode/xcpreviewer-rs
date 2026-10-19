from pathlib import Path
import os,sys,subprocess,json,hashlib
root=Path('/Users/8amps/xcpreviewer-rs'); work=Path(__file__).parent
sys.path.insert(0,str(root/'tools/re'))
from reloop.core import Controller
base=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin')
env=dict(os.environ,RUSTC=str(base/'rustc'),RUSTDOC=str(base/'rustdoc'),CARGO_TARGET_DIR=str(work/'rust-target'))
with Controller().lock():
 files=['src/binary_plist.rs','src/bin/decode-preview-payload.rs','tests/binary_plist.rs']
 for file in files: subprocess.run([str(base/'rustfmt'),'--edition','2021',str(root/'tools/re/rust/canvas-core'/file)],check=True,timeout=15)
 p=subprocess.run([str(base/'cargo'),'test','--offline','-p','canvas-core'],cwd=root,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
 (work/'rust-tests.log').write_text(p.stdout); print(p.stdout)
 if p.returncode: sys.exit(p.returncode)
 p=subprocess.run([str(base/'cargo'),'build','--offline','-p','canvas-core','--bin','decode-preview-payload'],cwd=root,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=45)
 (work/'rust-build.log').write_text(p.stdout); p.check_returncode()
 results=[]
 for name in ['payload-defaults','payload-explicit']:
  output=work/(name+'.bitmap')
  p=subprocess.run([str(work/'rust-target/debug/decode-preview-payload'),str(work/(name+'.bplist')),str(output)],capture_output=True,text=True,timeout=5)
  p.check_returncode(); assert 'width=3 height=2 stride=40 bytes=80 bitmap_info=8194 bits_per_component=8 bits_per_pixel=32' in p.stdout; assert ('corner=0 scale=3 regions=1' if name=='payload-defaults' else 'corner=6.5 scale=2 regions=1') in p.stdout; actual=output.read_bytes(); expected=(work/'expected-bitmap.bin').read_bytes()
  assert actual==expected
  results.append(dict(fixture=name,stdout=p.stdout.strip(),all_bytes_equal=True,bytes=len(actual),sha256=hashlib.sha256(actual).hexdigest(),synthetic_padding_bytes=56))
 (work/'cli-results.json').write_text(json.dumps(results,indent=2)+'\n'); print(json.dumps(results))

# Malformed input must fail before replacing an existing output artifact.
invalid=work/'invalid.bplist'; invalid.write_bytes(b'bplist00bad')
output=work/'preserve.bitmap'; output.write_bytes(b'previous valid output')
p=subprocess.run([str(work/'rust-target/debug/decode-preview-payload'),str(invalid),str(output)],capture_output=True,text=True,timeout=5)
assert p.returncode==1 and output.read_bytes()==b'previous valid output'
(work/'cli-negative.json').write_text(json.dumps({'exit':p.returncode,'stderr':p.stderr.strip(),'prior_output_preserved':True})+'\n')
