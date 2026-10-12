import json,hashlib
from pathlib import Path
CASES=[('emoji-exact',[(1,bytes.fromhex('f09f9880')*16384)]),('emoji-over',[(1,bytes.fromhex('f09f9880')*16384+b'x')]),('accent-exact',[(1,bytes.fromhex('c3a9')*32768)]),('accent-over',[(1,bytes.fromhex('c3a9')*32768+b'x')]),('invalid-exact',[(1,bytes([255])*65536)]),('incomplete',[(1,bytes.fromhex('f09f98'))]),('split-emoji',[(1,bytes([x])) for x in bytes.fromhex('f09f9880')]),('nul',[(1,bytes([x])) for x in [0,1,2,255,10,42,99,128]]),('invalid-stderr',[(2,bytes([255])*65536)]),('mixed-invalid',[(1,bytes.fromhex('f09f9880')*8192),(2,bytes([255])*32768)]),('over-then-ascii',[(1,bytes([255])*65537),(2,b'ok')]),('exact-then-over',[(2,bytes([255])*65536),(1,b'x')])]
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
 plans=[]
 for name,chunks in CASES:
  plan=[]
  for idx,(fd,raw) in enumerate(chunks):
   filename=name+'-'+str(idx)+'.raw';assert (e/filename).read_bytes()==raw;plan.append({'fd':fd,'file':filename,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
  plans.append({'name':name,'chunks':plan})
 assert json.loads((e/'prediction.json').read_text())=={'limit':65536,'repeats':2,'phases':['before','after'],'cases':plans,'source_injection_only':True,'native_cleanup_qualified':False}
 assert json.loads((e/'wait.json').read_text())=={'code':0,'stdout':'48 injected raw output controls pass\n','stderr':'','timeout':False}
 rows=json.loads((e/'results.json').read_text());assert len(rows)==48
 for phaseidx,phase in enumerate(['before','after']):
  for round in range(2):
   for idx,(name,chunks) in enumerate(CASES):
    x=rows[phaseidx*24+round*12+idx];rec=x['record'];out=b'';err=b'';reject=False
    for fd,raw in chunks:
     if len(out)+len(err)+len(raw)>65536:reject=True;continue
     if fd==1:out+=raw
     else:err+=raw
    raw=b''.join(b for _,b in chunks);assert x['name']==name and x['round']==round and x['phase']==phase and x['input_bytes']==len(raw) and x['input_sha256']==hashlib.sha256(raw).hexdigest()
    assert x['chunks']==[{'fd':fd,'bytes':len(b)} for fd,b in chunks] and x['retained_raw_bytes']==len(out)+len(err)
    assert rec['stdout']==out.decode('utf-8',errors='replace') and rec['stderr']==err.decode('utf-8',errors='replace') and x['text_utf8_bytes']==len(rec['stdout'].encode())+len(rec['stderr'].encode())
    assert x['error']==('Error: Observed compiler output limit' if reject else None) and x['writes']==(['abort\n'] if reject else []) and x['killCalls']==[{'pid':-900001,'sig':'SIGKILL'}]
    assert rec['privateAbortRequested'] is reject and rec['emergencyClosed'] is False and rec['pid']==900001 and rec['anchorCode'] is None and rec['signal']=='SIGKILL'
    assert rec['report']=={'kind':'complete','drained':True,'target_code':43 if reject else 0,'failure':'abort' if reject else None,'observations':1,'tracked':0,'remaining_observed':0,'scope':'Injected source fixture; no native process launched'}
    fields={'stdoutBytes':len(out),'stderrBytes':len(err),'stdoutSha256':hashlib.sha256(out).hexdigest(),'stderrSha256':hashlib.sha256(err).hexdigest()}
    for key,value in fields.items():
     if phase=='after':assert rec[key]==value
     else:assert key not in rec
 assert rows[28]['record']['stdoutBytes']==65536 and rows[28]['text_utf8_bytes']==196608
 assert rows[34]['record']['stderrBytes']==2 and rows[34]['record']['stdoutBytes']==0 and rows[34]['error']=='Error: Observed compiler output limit'
 env=json.loads((e/'environment.json').read_text());assert env['node_version']=='v24.19.0' and env['private_bridge_available'] is False
 return {'injected_controls':48,'exact_input_bytes_compared':sum(len(b) for _,chunks in CASES for _,b in chunks)*4,'native_processes':0,'raw_count_digest_fields':4}
