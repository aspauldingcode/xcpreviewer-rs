import hashlib,json
from pathlib import Path
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
 for n,x in m['files'].items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts;p=e/n;assert not p.is_symlink();raw=p.read_bytes();assert len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256']
 compile=json.loads((e/'compile.json').read_text());assert compile['code']==0 and compile['timeout'] is False
 def expected(seed):
  raw=bytearray([seed])*16384;raw[:1152]=bytes([165])*1152
  for y in range(9):
   for x in range(17):
    for c in range(4):raw[y*128+x*4+c]=255 if c==3 else (seed+x*17+y*31+c*53)&255
  return raw
 initial_bytes=expected(49);count=0;pids=[];repeats=[]
 names=['read-only','write-noop','active','padding','tail','restore']
 for mode in ['repeat-0','repeat-1']:
  root=e/mode;wait=json.loads((root/'wait.json').read_text());assert wait['code']==0 and wait['timeout'] is False and wait['stderr']=='';row=json.loads(wait['stdout']);assert type(row['pid']) is int and row['pid']>1 and type(row['surface_id']) is int and row['surface_id']>0;pids.append(row['pid'])
  for k,v in {'allocation_bytes':16384,'stride':128,'resource_name_removed':True,'all_cf_owners_released':True,'lookup_after_release':False,'distinct_alias':True}.items():assert row[k]==v and type(row[k]) is type(v)
  assert type(row['initial_seed']) is int and row['initial_seed']==1 and type(row['initial_alias_seed']) is int and row['initial_alias_seed']==1;assert len(row['steps'])==6
  frames={f'stage-0-alias-{i}.bin':bytes(initial_bytes) for i in range(2)};raw=bytearray(initial_bytes);seed=row['initial_seed']
  for i,name in enumerate(names):
   step=row['steps'][i];after=seed+(i!=0)
   for k,v in {'name':name,'writer_alias':i&1,'before':seed,'lock_seed':after,'unlock_seed':after,'after':after,'alias_after':after,'after_snapshots':after,'surface_id':row['surface_id'],'lock_code':0,'unlock_code':0}.items():assert step[k]==v and type(step[k]) is type(v)
   if i in [2,3,4]:raw[{2:0,3:68,4:16383}[i]]^=1
   if i==5:
    for offset in [0,68,16383]:raw[offset]^=1
   frames.update({f'stage-{i+1}-alias-{j}.bin':bytes(raw) for j in range(2)});seed=after
  assert raw==initial_bytes and seed==6 and {p.name for p in root.glob('*.bin')}==set(frames)
  observed={}
  for name,expected_bytes in frames.items():observed[name]=(root/name).read_bytes();assert observed[name]==expected_bytes;count+=1
  repeats.append(observed)
 assert pids[0]!=pids[1] and repeats[0]==repeats[1] and count==28
 env=json.loads((e/'environment.json').read_text());rea=json.loads((e/'rea.json').read_text());assert rea['open']['result']['sha256']==rea['identity']['result']['sha256']==env['helper_sha256']=='ec70942f90a992de56e595bec6f643afc00e2d13ad0915c5b772a1b3459124b3' and rea['identity']['result']['architecture']=='arm64' and rea['closed']['result'] is None
 return {'allocations':count,'full_allocation_bytes':count*16384,'padding_bytes':count*540,'tail_bytes':count*15232,'fresh_repeats':2,'no_op_seed_changes':2,'seed_update_timing':'not resolved by returned lock/unlock seeds','canvas_generation':False}
