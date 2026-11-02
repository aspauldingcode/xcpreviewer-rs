from pathlib import Path
import subprocess,plistlib,json,hashlib,struct,os
from PIL import Image
w=Path(__file__).parent;base=Path('/private/tmp/swiftui-source-preview-20261027')
env={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')}
names=['bars','transparent','factory','provider']
inputs=[{'kind':'render','case':name,'input':plistlib.loads((w/(name+'.bplist')).read_bytes())} for name in names]
(w/'input.bplist').write_bytes(plistlib.dumps(inputs,fmt=plistlib.FMT_BINARY))
r=subprocess.run([str(base/'native'),str(w/'input.bplist'),str(w/'native.bplist')],capture_output=True,env=env,timeout=8);(w/'native.stderr').write_bytes(r.stderr);r.check_returncode()
n=plistlib.loads((w/'native.bplist').read_bytes());assert n['destroyedValues']==n['destroyedPlists']==4 and n['releasedErrors']==0
rows=[]
for name,item,native in zip(names,inputs,n['rows']):
 assert native['accepted'] and native['canonical']==item['input']
 p=(w/(name+'.bplist')).read_bytes()
 a=subprocess.run([str(base/'target/debug/canvas-frame')],input=p,capture_output=True,check=True,timeout=5).stdout
 b=subprocess.run(['node',str(base/'run-wasi.cjs'),str(base/'target/wasm32-wasip1/debug/canvas-frame.wasm')],input=p,capture_output=True,check=True,timeout=10).stdout
 assert a==b and a[:8]==b'XCPV\x01\0\0\0' and struct.unpack_from('<4I',a,8)==(96,64,24576,0) and struct.unpack_from('<d',a,24)[0]==2
 rgba=Image.open(w/(name+'.png')).convert('RGBA').tobytes()
 projected=bytes(c for r,g,b,alpha in zip(*[iter(rgba)]*4) for c in ((r*alpha+127)//255,(g*alpha+127)//255,(b*alpha+127)//255,alpha))
 assert a[40:]==projected
 if name=='bars' or name=='factory':assert projected==bytes([255,0,0,255])*96*32+bytes([0,0,255,255])*96*32
 if name=='transparent':assert projected==bytes([96,32,64,128])*96*64
 (w/(name+'.packet')).write_bytes(a)
 rows.append({'case':name,'native_codec_accepted':True,'canonical_equal':True,'host_wasi_equal':True,'native_png_projection_equal':True,'rgba_bytes':24576,'rgba_sha256':hashlib.sha256(projected).hexdigest()})
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[base/'native',base/'target/debug/canvas-frame',base/'target/wasm32-wasip1/debug/canvas-frame.wasm',base/'run-wasi.cjs']
(w/'transport-results.json').write_text(json.dumps({'rows':rows,'dependencies':{str(p):sha(p) for p in files},'scope':'Existing qualified native RenderPayload codec and host/WASIp1 converters reused with pinned executables; not rebuilt.'},indent=2)+'\n')
print(json.dumps(rows))
