import json,hashlib
from pathlib import Path
CASES=[('emoji-exact',bytes.fromhex('f09f9880')*16384,False),('emoji-over',bytes.fromhex('f09f9880')*16384+b'x',False),('accent-exact',bytes.fromhex('c3a9')*32768,False),('accent-over',bytes.fromhex('c3a9')*32768+b'x',False),('invalid-exact',bytes([255])*65536,False),('incomplete',bytes.fromhex('f09f98'),False),('split-emoji',bytes.fromhex('f09f9880'),True),('nul',bytes([0,1,2,255,10,42,99,128]),True)]
def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text());assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,item in m['files'].items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts;p=e/name;assert not p.is_symlink();b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
 assert json.loads((e/'wait.json').read_text())=={'code':0,'stdout':'16 injected Unicode output controls pass\n','stderr':'','timeout':False}
 pred=json.loads((e/'prediction.json').read_text());assert pred=={'cases':[{'name':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'split':split,'reject':len(b)>65536} for n,b,split in CASES],'limit':65536,'repeats':2,'source_injection_only':True,'native_cleanup_qualified':False}
 rows=json.loads((e/'results.json').read_text());assert len(rows)==16
 for round in range(2):
  for idx,(n,raw,split) in enumerate(CASES):
   assert (e/(n+'.raw')).read_bytes()==raw;x=rows[round*8+idx];reject=len(raw)>65536;kept=b'' if reject else raw;text=kept.decode('utf-8',errors='replace');rec=x['record']
   assert x['name']==n and x['round']==round and x['input_bytes']==len(raw) and x['input_sha256']==hashlib.sha256(raw).hexdigest()
   assert x['error']==('Error: Observed compiler output limit' if reject else None);assert x['writes']==(['abort\n'] if reject else []) and x['killCalls']==[{'pid':-900001,'sig':'SIGKILL'}]
   assert x['chunks']==([1]*len(raw) if split else [len(raw)]) and x['retained_raw_bytes']==len(kept)
   assert rec['stdout']==text and rec['stderr']=='' and x['text_utf8_bytes']==len(text.encode()) and x['text_utf16_units']==len(text.encode('utf-16-le'))//2
   assert rec['privateAbortRequested'] is reject and rec['emergencyClosed'] is False and rec['signal']=='SIGKILL' and rec['pid']==900001 and rec['anchorCode'] is None
   assert rec['report']=={'kind':'complete','drained':True,'target_code':43 if reject else 0,'failure':'abort' if reject else None,'observations':1,'tracked':0,'remaining_observed':0,'scope':'Injected source fixture; no native process launched'}
 assert rows[4]['retained_raw_bytes']==65536 and rows[4]['text_utf8_bytes']==196608 and rows[5]['retained_raw_bytes']==3 and rows[5]['text_utf8_bytes']==3
 env=json.loads((e/'environment.json').read_text());assert env['node_version']=='v24.19.0' and env['private_bridge_available'] is False and env['prior_manifest_sha256']=='a834e8daa1bfdb0211f6460ca095318c9cd3a7a0233f1cf64dddb37026e22125'
 return {'injected_controls':16,'invalid_raw_bytes':65536,'invalid_text_bytes':196608,'native_processes':0,'exact_raw_bytes_compared':sum(len(b) for _,b,_ in CASES)*2}
