from pathlib import Path
import subprocess,plistlib,json,hashlib,struct,os
from PIL import Image
w=Path(__file__).parent
base=Path('/private/tmp/swiftui-source-preview-20261027')
env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')}
input=[{'kind':'render','case':'provider','input':plistlib.loads((w/'provider.bplist').read_bytes())}]
(w/'input.bplist').write_bytes(plistlib.dumps(input,fmt=plistlib.FMT_BINARY))
r=subprocess.run([str(base/'native'),str(w/'input.bplist'),str(w/'native.bplist')],capture_output=True,env=env,timeout=8)
(w/'native.stderr').write_bytes(r.stderr);r.check_returncode()
n=plistlib.loads((w/'native.bplist').read_bytes());assert n['destroyedValues']==n['destroyedPlists']==1 and n['releasedErrors']==0 and n['rows'][0]['accepted'] and n['rows'][0]['canonical']==input[0]['input']
p=(w/'provider.bplist').read_bytes()
a=subprocess.run([str(base/'target/debug/canvas-frame')],input=p,capture_output=True,check=True,timeout=5).stdout
b=subprocess.run(['node',str(base/'run-wasi.cjs'),str(base/'target/wasm32-wasip1/debug/canvas-frame.wasm')],input=p,capture_output=True,check=True,timeout=10).stdout
assert a==b and a[:8]==b'XCPV\x01\0\0\0' and struct.unpack_from('<4I',a,8)==(96,64,24576,0) and struct.unpack_from('<d',a,24)[0]==2
png=Image.open(w/'provider.png').convert('RGBA').tobytes()
assert png==a[40:]==(bytes([255,0,0,255])*96*32+bytes([0,0,255,255])*96*32)
(w/'provider.packet').write_bytes(a)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[base/'native',base/'target/debug/canvas-frame',base/'target/wasm32-wasip1/debug/canvas-frame.wasm',base/'run-wasi.cjs']
r={'native_codec_accepted':True,'canonical_equal':True,'native_values_destroyed':1,'native_plists_destroyed':1,'host_wasi_equal':True,'native_png_equal':True,'rgba_bytes':24576,'rgba_sha256':hashlib.sha256(a[40:]).hexdigest(),'dependencies':{str(p):sha(p) for p in files},'runtime_images':n['runtimeImages']}
(w/'transport-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['dependencies','runtime_images']}))
