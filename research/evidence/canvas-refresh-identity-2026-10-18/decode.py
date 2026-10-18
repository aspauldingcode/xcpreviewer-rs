"""Decode owned process/state telemetry; not a reconstruction pixel oracle."""
import hashlib,json
from pathlib import Path
from PIL import Image
BLACK=(0,0,0,255)
COLORS=[(255,0,255,255),(255,0,0,255),(0,255,0,255),(0,0,255,255)]
def need(ok,message):
 if not ok:raise ValueError(message)
def decode(path):
 image=Image.open(path).convert('RGBA');need(image.size==(512,96),'geometry');raw=image.tobytes();bands=[]
 for row,color in enumerate(COLORS):
  bits=[]
  for column in range(128):
   pixel=image.getpixel((column*4,row*24));need(pixel in [BLACK,color],'palette')
   bit=pixel==color;bits.append(bit)
   # Every pixel of every cell is checked against its sampled telemetry symbol.
   for y in range(row*24,(row+1)*24):
    for x in range(column*4,(column+1)*4):need(image.getpixel((x,y))==pixel,'cell nonuniform')
  bands.append(bits)
 need(bands[0]==[(i//4)%2==0 for i in range(128)],'sentinel')
 need(all(bands[1][i*32:(i+1)*32]==bands[1][:32] for i in range(4)),'PID copies')
 number=lambda b:sum(int(v)<<(len(b)-1-i) for i,v in enumerate(b))
 pid=number(bands[1][:32]);need(1<pid<=2147483647,'PID domain')
 need(bands[3]==[not b for b in bands[2]],'token complement')
 token='%032x'%number(bands[2]);need(token!='0'*32,'zero token')
 return {'pid':pid,'state_token_hex':token,'rgba_sha256':hashlib.sha256(raw).hexdigest(),'rgba_bytes_checked':len(raw),'telemetry_derived_expectation':True,'native_cause_proven':False}
if __name__=='__main__':
 import sys
 print(json.dumps(decode(Path(sys.argv[1]))))
