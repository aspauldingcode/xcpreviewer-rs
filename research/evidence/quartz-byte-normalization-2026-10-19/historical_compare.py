"""Predeclared reciprocal model for sealed holdouts; never replace old admission."""
from pathlib import Path
import hashlib,json,math,struct
from predictions import f32
BASE=Path('/Users/8amps/xcpreviewer-rs/research/evidence/color-holdout-gate-recovery-2026-10-18')
def compare():
 if hashlib.sha256((BASE/'seal.json').read_bytes()).hexdigest()!='eafb11df59f30a00c61c406c6698ce98dc7b3da520295b1f280900845d6db9e6':raise ValueError('Historical seal drift')
 seal=json.loads((BASE/'seal.json').read_text())
 for name,h in seal['files'].items():
  if hashlib.sha256((BASE/name).read_bytes()).hexdigest()!=h:raise ValueError('Historical bytes drift')
 rows=[]
 for mode in range(2):
  for phase,rgb in enumerate([[.0625,.375,.8125],[.2,.6,.9],[.0625,.375,.8125]]):
   if mode==0:
    codes=[int(math.floor((12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055)*255+.5)) for x in rgb]+[255];expected_provider=bytes(codes)*153;channels=[f32(f32(k)*f32(1/255)) for k in codes]
   else:
    pixel=struct.pack('<4e',*rgb,1);expected_provider=pixel*153;channels=struct.unpack('<4e',pixel)
   expected=bytearray(b'\xa5'*4096);pixel=struct.pack('<4f',*channels)
   for y in range(9):expected[y*288:y*288+272]=pixel*17
   path=BASE/'export/owned-documents';provider=(path/('mode%d-phase%d-provider.raw'%(mode,phase))).read_bytes();actual=(path/('mode%d-phase%d-readback.raw'%(mode,phase))).read_bytes()
   rows.append({'mode':mode,'phase':phase,'provider_matches':provider==expected_provider,'readback_mismatch_bytes':sum(x!=y for x,y in zip(actual,expected)),'readback_length':len(actual)})
 return {'predeclared_reciprocal_comparison':rows,'old_strict_export_admission_changed':False,'renderer_internal_cause_proven':False,'display_qualified':False,'canvas_qualified':False}
if __name__=='__main__':print(json.dumps(compare()))
