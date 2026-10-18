import hashlib,json
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parent
seal=json.loads((root/'seal.json').read_text())
for name,digest in seal['files'].items():
 p=root/name
 if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError(name)
raws={}
checks=json.loads((root/'pixel-checks.json').read_text())
for row in checks['snapshots']:
 image=Image.open(root/(row['name']+'.png')).convert('RGBA');raw=image.tobytes();raws[row['name']]=raw
 if image.size!=(320,200) or hashlib.sha256(raw).hexdigest()!=row['rgba_sha256']:raise ValueError('pixels')
 if any(list(image.getpixel(xy))!=row['expected_corner_rgba'] for xy in [(0,0),(319,0),(0,199),(319,199)]):raise ValueError('corners')
 if any(raw[i]!=255 for i in range(3,len(raw),4)):raise ValueError('alpha')
if raws['dark-initial']!=raws['dark-restored'] or raws['dark-initial']==raws['light']:raise ValueError('variants')
after=json.loads((root/'after-cleanup.json').read_text())
if after['owned_workspace_windows']!=0 or not after['bridge_status']['running'] or not after['bridge_status']['responsive']:raise ValueError('recorded cleanup')
if hashlib.sha256((root/'owned-source.swift').read_bytes()).hexdigest()!=after['source_sha256']:raise ValueError('source changed')
print(json.dumps({'verified':True,'files':len(seal['files']),'dark_repeat_rgba_bytes':256000,'live_endpoint_rechecked':False}))
