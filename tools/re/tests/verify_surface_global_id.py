import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 good=json.loads((e/'compile.json').read_text());assert good['code']==0 and good['timeout'] is False
 def expected(seed):
  raw=bytearray([seed])*16384;raw[:1152]=bytes([165])*1152
  for y in range(9):
   for x in range(17):
    for c in range(4):raw[y*128+x*4+c]=255 if c==3 else (seed+x*17+y*31+c*53)&255
  return raw
 old,new=expected(49),expected(50);total=0;pids=[]
 for name in ['released-0','held','released-1']:
  root=e/name;wait=json.loads((root/'wait.json').read_text());assert wait['code']==0 and wait['timeout'] is False and wait['stderr']=='';row=json.loads(wait['stdout']);held=name=='held';pids.append(row['pid']);assert row['pid']>1 and type(row['old_id']) is int and row['old_id']>0
  for k,v in {'mode':'held' if held else 'released','stride':128,'allocation_bytes':16384,'owner_cf_released':True,'right_held_during_churn':held,'right_refs_during_churn':1 if held else 0,'before_lookup_present':held,'attempts':64 if held else 1,'matched':not held,'port_released':True,'settled_lookup_present':False}.items():assert row[k]==v and type(row[k]) is type(v)
  ids=row['candidate_ids'];assert len(ids)==row['attempts'] and all(type(x) is int and x>0 for x in ids) and (all(x!=row['old_id'] for x in ids) if held else ids==[row['old_id']])
  frames={'initial.bin':old,**{f'candidate-{i:03d}.bin':new for i in range(row['attempts'])}}
  frames.update({'lookup-before.bin':old,'retained-lookup.bin':old} if held else {'stale-lookup.bin':new})
  assert {p.name for p in root.glob('*.bin')}==set(frames)
  for file,raw in frames.items():observed=(root/file).read_bytes();assert observed==raw;total+=len(observed)
 assert len(set(pids))==3 and total==1196032
 for name in ['initial.bin','candidate-000.bin','stale-lookup.bin']:assert (e/'released-0'/name).read_bytes()==(e/'released-1'/name).read_bytes()
 env=json.loads((e/'environment.json').read_text());rea=json.loads((e/'rea.json').read_text());assert rea['open']['result']['sha256']==rea['identity']['result']['sha256']==env['helper_sha256']=='32ad6fd9113ed145fd1f413d16dc8ab03259b3aae04448ff39b7c2c9daf33d8f' and rea['identity']['result']['architecture']=='arm64' and rea['closed']['result'] is None
 return {'full_allocation_bytes':total,'allocations':73,'padding_bytes':39420,'tail_bytes':1111936,'released_id_alias_controls':2,'retained_right_creation_controls':64,'physical_reclamation':False}
