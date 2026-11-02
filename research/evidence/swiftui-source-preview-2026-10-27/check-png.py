from pathlib import Path
from PIL import Image
import plistlib,json,hashlib
w=Path(__file__).parent;rows=[]
for name in ['sample','asymmetric','transparent']:
 p=plistlib.loads((w/(name+'.bplist')).read_bytes());raw=p['bitmapDescription']['data'];rgba=bytes(c for b,g,r,a in zip(*[iter(raw)]*4) for c in (r,g,b,a));reference=Image.open(w/(name+'.png')).convert('RGBA').tobytes();premult=bytes(c for r,g,b,a in zip(*[iter(reference)]*4) for c in ((r*a+127)//255,(g*a+127)//255,(b*a+127)//255,a));assert rgba==premult;(w/(name+'.rgba')).write_bytes(rgba);rows.append({'case':name,'bytes':len(rgba),'independent_png_premultiplied_equal':True,'sha256':hashlib.sha256(rgba).hexdigest()})
(w/'png-results.json').write_text(json.dumps(rows,indent=2)+'\n');print('Compared',sum(x['bytes'] for x in rows),'pixel bytes')
