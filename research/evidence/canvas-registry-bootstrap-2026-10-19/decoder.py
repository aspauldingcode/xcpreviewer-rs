"""Independent byte expectations for the owned callback probe, not Canvas wire."""
import json,os,re,stat
from pathlib import Path

def need(value,message):
 if not value:raise ValueError(message)
def expected(identity,event,sequence,count):
 need(type(identity) is dict and set(identity)=={'nonce','pid','view'},'identity keys')
 need(type(identity['nonce']) is str and re.fullmatch('[0-9a-f]{32}',identity['nonce']),'nonce')
 need(type(identity['pid']) is int and 1<identity['pid']<2**31,'pid')
 need(type(identity['view']) is str and re.fullmatch('[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',identity['view']),'view')
 need(event in ('appear','increment') and type(sequence) is int and 0<=sequence<=3 and type(count) is int and 0<=count<=3,'event domain')
 return {**identity,'schema':1,'event':event,'sequence':sequence,'count':count}
def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode('ascii')
def filename(value):return 'pid-%d-view-%s-sequence-%d.json'%(value['pid'],value['view'],value['sequence'])
def record(raw,name,identity,event,sequence,count):
 need(type(raw) is bytes and len(raw)<=512,'record bytes')
 value=expected(identity,event,sequence,count)
 need(name==filename(value),'filename binding')
 need(raw==canonical(value),'exact canonical bytes/transcript')
 return value
def directory(root,identity,increments):
 need(type(increments) is int and 0<=increments<=3,'increment scope')
 root=Path(root);need(not root.is_symlink() and root.is_dir(),'root')
 entries=list(root.iterdir());need(len(entries)==increments+1,'record count/pending files')
 wants=[expected(identity,'appear' if i==0 else 'increment',i,i) for i in range(increments+1)]
 need({p.name for p in entries}=={filename(v) for v in wants},'directory namespace')
 result=[]
 for value in wants:
  p=root/filename(value);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
  try:
   info=os.fstat(fd);need(stat.S_ISREG(info.st_mode) and info.st_size<=512,'regular bounded file')
   raw=os.read(fd,513)
  finally:os.close(fd)
  result.append(record(raw,p.name,identity,value['event'],value['sequence'],value['count']))
 return result
