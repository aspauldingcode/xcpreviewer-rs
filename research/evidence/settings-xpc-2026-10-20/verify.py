"""Verify owned semantic expectations and exact opaque archive preservation."""
from pathlib import Path
import json,base64,copy,sys,hashlib
FLAGS=[{}, {0:True,42:True}, {0:True,42:False}, {0:True,42:True,65535:True}]
OBJECTS=[{}, {1:'owned',65535:[1,'two']}, {65535:[1,'two']}, {0:'replacement',1:'owned',65535:[1,'two']}]
def verify(rows):
 assert len(rows)==4
 total=0; archives={}
 for i,row in enumerate(rows):
  assert row['mode']==i;x=row['xpc'];assert x['type']=='dictionary';d=x['value'];assert set(d)==(set() if i==0 else {'flags','objects'})
  flags={};objects={}
  for e in d.get('flags',{'value':[]})['value']:
   assert e['type']=='array';p=e['value'];assert len(p)==2 and p[0]['type']=='uint64' and p[1]['type']=='bool';k=int(p[0]['value']);assert k not in flags;flags[k]=p[1]['value']
  assert flags==FLAGS[i]
  for e in d.get('objects',{'value':[]})['value']:
   assert e['type']=='array';p=e['value'];assert len(p)==3 and p[0]['type']=='uint64' and p[1]['type']=='dictionary' and p[2]=={'type':'int64','value':2}
   k=int(p[0]['value']);assert k not in objects;obj=p[1]['value'];assert set(obj)=={'root'};root=obj['root'];assert root['type']=='data';b=base64.b64decode(root['base64'],validate=True);assert len(b)==root['bytes'] and b.startswith(b'bplist17');total+=len(b);objects[k]=b
   value=json.dumps(OBJECTS[i][k],sort_keys=True);prior=archives.setdefault(value,b);assert prior==b
  assert set(objects)==set(OBJECTS[i])
  for k in [0,1,42,65535]:assert row['roundtrip'][str(k)]=={'flag':int(FLAGS[i][k]) if k in FLAGS[i] else 9223372036854775807,'object':OBJECTS[i].get(k)}
 assert total==447
 return {'native_cases':4,'opaque_archive_bytes_preserved':total,'separate_flag_object_namespaces':True,'absent_flag_sentinel':9223372036854775807,'native_owned_roundtrip':True}
if __name__=='__main__':
 rows=json.loads(Path(sys.argv[1]).read_text());result=verify(rows);mutants=[]
 for kind in range(7):
  x=copy.deepcopy(rows)
  if kind==0:x[1]['roundtrip']['0']['flag']=7
  elif kind==1:x[2]['xpc']['value']['flags']['value'][1]['value'][1]['value']=True
  elif kind==2:x[3]['xpc']['value']['objects']['value'].pop(0)
  elif kind==3:x[1]['xpc']['value']['objects']['value'][0]['value'][2]['value']=1
  elif kind==4:x[1]['xpc']['value']['objects']['value'][0]['value'][1]['value']['root']['bytes']-=1
  elif kind==5:x[2]['roundtrip']['65535']['object']=[2,'two']
  else:x[2]['xpc']['value']['objects']['value'][0]['value'][1]['value']['root']['base64']=base64.b64encode(b'broken').decode()
  try:verify(x)
  except (AssertionError,KeyError,ValueError):mutants.append(kind)
 assert len(mutants)==7;result['receipt_mutants_rejected']=len(mutants);print(json.dumps(result))
