from pathlib import Path
import subprocess,plistlib,json,hashlib,struct,os
from PIL import Image
w=Path(__file__).parent;base=Path('/private/tmp/swiftui-source-preview-20261027')
env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')}
value=plistlib.loads((w/'frame.bplist').read_bytes());(w/'input.bplist').write_bytes(plistlib.dumps([{'kind':'render','case':'watched-frame','input':value}],fmt=plistlib.FMT_BINARY))
r=subprocess.run([str(base/'native'),str(w/'input.bplist'),str(w/'native.bplist')],capture_output=True,env=env,timeout=8);(w/'native.stderr').write_bytes(r.stderr);r.check_returncode();n=plistlib.loads((w/'native.bplist').read_bytes());assert n['destroyedValues']==n['destroyedPlists']==1 and n['releasedErrors']==0 and n['rows'][0]['accepted'] and n['rows'][0]['canonical']==value
payload=(w/'frame.bplist').read_bytes();host=subprocess.run([str(base/'target/debug/canvas-frame')],input=payload,capture_output=True,check=True,timeout=5).stdout
wasm=subprocess.run(['node',str(base/'run-wasi.cjs'),str(base/'target/wasm32-wasip1/debug/canvas-frame.wasm')],input=payload,capture_output=True,check=True,timeout=10).stdout
assert host==wasm and host[:8]==b'XCPV\x01\0\0\0' and struct.unpack_from('<4I',host,8)==(32,24,3072,0) and struct.unpack_from('<d',host,24)[0]==1
rgba=Image.open(w/'reference.png').convert('RGBA').tobytes();projected=bytes(c for r,g,b,a in zip(*[iter(rgba)]*4) for c in ((r*a+127)//255,(g*a+127)//255,(b*a+127)//255,a));assert host[40:]==projected
(w/'frame.packet').write_bytes(host)
files=[base/'native',base/'target/debug/canvas-frame',base/'target/wasm32-wasip1/debug/canvas-frame.wasm',base/'run-wasi.cjs'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={'native_codec_accepted':True,'canonical_equal':True,'native_png_projection_equal':True,'host_wasi_equal':True,'rgba_bytes':len(projected),'rgba_sha256':hashlib.sha256(projected).hexdigest(),'dependencies':{str(p):sha(p) for p in files},'scope':'Inherited native codec and host/WASIp1 converters reused with pinned binaries; not rebuilt. No new browser readback or Rust test rerun.'};(w/'transport-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
