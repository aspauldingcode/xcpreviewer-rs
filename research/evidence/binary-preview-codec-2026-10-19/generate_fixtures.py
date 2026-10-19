"""Independent stdlib bplist fixtures; no parser implementation is imported."""
import hashlib,json,plistlib
from pathlib import Path
work=Path(__file__).parent
bitmap=bytes((i*37+11)%256 for i in range(80))
obj={'bitmapDescription':{'data':bitmap,'width':3,'height':2,'bytesPerRow':40,'byteOrder':'little'},'selectableRegions':[{'path':'root/按钮/🧪','rect':{'x':-1.5,'y':2.0,'width':3.25,'height':4.5},'serializedAccessibilityElement':b'\x00\xff\x00\x07'}]}
fixtures={'payload-defaults':obj,'payload-explicit':dict(obj,scaleFactor=2.0,snapshotCornerRadius=6.5),'unicode':{'text':'a'*20+'按钮🧪','positive':65535,'negative':-7,'false':False,'true':True,'null':None,'float32-compatible':1.25,'data':bytes(range(256))*2},'wide-references':['item-'+str(i) for i in range(300)]}
provenance={'producer':'Python standard-library plistlib binary serializer','fixtures':{},'native_claim':False,'bitmap_bytes':80,'active_per_row':12,'padding_per_row':28,'rows':2}
for name,value in fixtures.items():
 data=plistlib.dumps(value,fmt=plistlib.FMT_BINARY,sort_keys=False)
 p=work/(name+'.bplist')
 if p.exists(): assert p.read_bytes()==data, 'fixture changed: '+name
 p.write_bytes(data)
 provenance['fixtures'][name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
(work/'expected-bitmap.bin').write_bytes(bitmap)
(work/'fixture-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
