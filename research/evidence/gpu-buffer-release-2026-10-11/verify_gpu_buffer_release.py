import base64,hashlib,json
from pathlib import Path

def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for n,x in m['files'].items():
  p=e/n;assert not Path(n).is_absolute() and '..' not in Path(n).parts and not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 assert json.loads((e/'compile.json').read_text())['wait']==0
 pred=json.loads((e/'prediction.json').read_text());assert pred['parent_manifest_sha256']=='0841c787c1afff6c0da6833cb5dd78dd5f82ed02c2669e948ae09a71109c615c' and pred['subprocess_deadline_seconds']==15
 env=json.loads((e/'environment.json').read_text());assert env['machine'].strip()=='arm64' and '26.6' in env['xcode'] and '25F80' in env['sw_vers']
 rea=json.loads((e/'rea.json').read_text());assert rea['inspection']['subject']['digest']['sha256']==env['helper_sha256'] and rea['inspection']['provider']['id']=='native-macos' and rea['open']['result']['sha256']==env['helper_sha256'];assert rea['closed'] is True and rea['identity']['server_identity']['package']['version']=='6.2.0'
 def integer(x,v):assert type(x) is int and x==v
 raw_previous=None;all_bytes=0
 for i in range(2):
  assert json.loads((e/f'wait-{i}.json').read_text())=={'code':0,'timeout':False,'stderr':''}
  d=json.loads((e/f'result-{i}.json').read_text());integer(d['allocation_bytes'],16384);integer(d['row'],256);integer(d['width_bytes'],44);integer(d['height'],6);integer(d['wait_ns'],20000000);integer(d['completion_ns'],5000000000);assert d['unified_memory'] is True and d['device']=='Apple M1'
  assert [x['mode'] for x in d['rows']]==['encoded-uncommitted','committed-timeout'];raw=[]
  for committed,row in enumerate(d['rows']):
   for k in ['retained_references','error_absent','weak_alive_after_cpu_drop','weak_alive_before_pool_drain']:assert row[k] is True
   for k in ['weak_buffer_alive_after_pool_drain','weak_command_alive_after_pool_drain']:assert row[k] is False
   t=row['token_before'];assert type(t) is int and t>0 and row['token_after_cpu_drop']==t and row['token_before_pool_drain']==t
   integer(row['callback_count'],committed);integer(row['status'],4 if committed else 0);integer(row['event_after'],committed)
   if committed:
    assert row['timeout_observed'] is True and row['weak_alive_pending'] is True;integer(row['callbacks_before_release'],0);integer(row['event_before_release'],0);assert type(row['status_before_release']) is int and row['status_before_release'] in [2,3]
   before=bytes([0x5c]*16384);after=bytearray(before)
   if committed:
    for y in range(6):after[y*256:y*256+44]=bytes([0x77]*44)
   for key,wanted in [('before',before),('after',bytes(after))]:
    b=base64.b64decode(row[key],validate=True);assert b==wanted;raw.append(b);all_bytes+=len(b)
  if raw_previous is not None:assert raw==raw_previous
  raw_previous=raw
 assert all_bytes==131072
 return {'complete_bytes':all_bytes,'repetitions':2,'post_pool_weak_nil_cases':4}
