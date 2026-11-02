from pathlib import Path
import hashlib,json,struct,fcntl,os
from macho import Image
with open(Path(os.environ['XCPREVIEWER_ROOT'])/'research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 image=Image(Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsFoundationHost.framework/Versions/A/PreviewsFoundationHost'))
 assert hashlib.sha256(image.data).hexdigest()=='1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d'
 assert image.uuid=='6b75229bde5d3d3794bc75af4f4704c6'
 base=0x1581a4;_,size,count=struct.unpack('<HHI',image.read(base+8,8));assert size==12 and count==5
 record=base+16+size
 field=record+8;dest=field+struct.unpack('<i',image.read(field,4))[0];assert image.read(dest,4)==b'log\0'
 field=record+4;dest=field+struct.unpack('<i',image.read(field,4))[0];typeref=image.read(dest,32).split(b'\0',1)[0];assert typeref==b'SS7message_t'
 print(json.dumps({'classification':'minimum existing-case runtime input qualification','case':'log','associated_typeref':typeref.decode(),'associated_type':'(message: Swift.String)','field_descriptor':hex(base),'case_index':1,'image_uuid':image.uuid}))
