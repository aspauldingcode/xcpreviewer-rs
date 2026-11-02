from pathlib import Path
import subprocess,plistlib,hashlib,struct,json
w=Path(__file__).parent
native=plistlib.loads((w/'native.bplist').read_bytes());assert native['destroyedValues']==native['destroyedPlists']==3 and native['releasedErrors']==0
rows={x['case']:x for x in native['rows']};results=[]
for name in ['sample','asymmetric','transparent']:
 p=plistlib.loads((w/(name+'.bplist')).read_bytes());n=rows[name];assert n['accepted'] and n['canonical']==p
 args=[str(w/'target/debug/canvas-frame')];a=subprocess.run(args,input=(w/(name+'.bplist')).read_bytes(),capture_output=True,check=True,timeout=5).stdout
 b=subprocess.run(['node',str(w/'run-wasi.cjs'),str(w/'target/wasm32-wasip1/debug/canvas-frame.wasm')],input=(w/(name+'.bplist')).read_bytes(),capture_output=True,check=True,timeout=10).stdout;assert a==b and a[:8]==b'XCPV\x01\0\0\0'
 width,height,length,count=struct.unpack_from('<4I',a,8);assert count==0 and (width,height)==(p['bitmapDescription']['width'],p['bitmapDescription']['height']);assert struct.unpack_from('<d',a,24)[0]==p['scaleFactor'];assert a[40:]==(w/(name+'.rgba')).read_bytes();(w/(name+'.packet')).write_bytes(a)
 results.append({'case':name,'size':[width,height],'native_codec_accepted':True,'host_wasi_packet_equal':True,'pixel_bytes':length,'rgba_sha256':hashlib.sha256(a[40:]).hexdigest()})
(w/'packet-results.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
