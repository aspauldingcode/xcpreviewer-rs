import base64,hashlib,json
from pathlib import Path

def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for n,x in m['files'].items():
  p=e/n;assert not Path(n).is_absolute() and '..' not in Path(n).parts and not p.is_symlink();b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 assert json.loads((e/'compile.json').read_text())['wait']==0
 env=json.loads((e/'environment.json').read_text());assert env['machine'].strip()=='arm64' and '26.6' in env['xcode'] and '25F80' in env['sw_vers']
 rea=json.loads((e/'rea.json').read_text());assert rea['inspection']['subject']['digest']['sha256']==env['helper_sha256'] and rea['inspection']['provider']['id']=='native-macos' and rea['open']['result']['sha256']==env['helper_sha256'];assert rea['retainedToolValidationFailure']['acceptance'] is False
 def expected(base,color=None):
  b=bytearray([base]*16384)
  if color is not None:
   for y in range(6):b[y*256:y*256+44]=bytes([color]*44)
  return bytes(b)
 def integer(x,v):assert type(x) is int and x==v
 all_bytes=0;previous=None
 for i in range(2):
  assert json.loads((e/f'wait-{i}.json').read_text())=={'code':0,'timeout':False,'stderr':''}
  d=json.loads((e/f'result-{i}.json').read_text());integer(d['allocation_bytes'],16384);integer(d['row'],256);integer(d['width_bytes'],44);integer(d['height'],6);integer(d['wait_ns'],20000000);integer(d['completion_ns'],5000000000);assert d['unified_memory'] is True and d['device']=='Apple M1'
  tokens=d['resources_before'];assert len(tokens)==5 and all(type(t) is int and t>0 for t in tokens) and len(set(tokens))==5 and d['resources_after']==tokens
  a,b,c=d['first'],d['stale'],d['fresh'];integer(a['pending'],1);integer(a['callbacks_before_release'],0);assert type(a['status_before_release']) is int and a['status_before_release'] in [2,3];integer(a['event_before_release'],0);integer(a['event_after'],2)
  for x in [a,c]:integer(x['writer_calls'],1);integer(x['writer_status'],4)
  for x in [a,b,c]:integer(x['reader_calls'],1);integer(x['reader_status'],4)
  integer(b['writer_calls'],0);integer(b['event'],2);integer(c['event'],4)
  pairs=[(d['source_before'],expected(0xa5)),(d['destination_before'],expected(0x5c)),(a['source'],expected(0xa5,0x22)),(a['destination'],expected(0x5c,0x22)),(b['destination'],expected(0x5c,0x22)),(c['source'],expected(0xa5,0x77)),(c['destination'],expected(0x5c,0x77))]
  raw=[base64.b64decode(x,validate=True) for x,_ in pairs]
  for actual,(_,wanted) in zip(raw,pairs):assert actual==wanted;all_bytes+=len(actual)
  if previous is not None:assert raw==previous
  previous=raw
 assert all_bytes==229376
 return {'complete_bytes':all_bytes,'repetitions':2,'stale_event_counterexamples':2}
