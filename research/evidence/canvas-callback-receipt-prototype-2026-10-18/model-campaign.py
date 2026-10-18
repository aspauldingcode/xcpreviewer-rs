"""Portable receipt admission controls; all inputs here are synthetic."""
import json,base64,hashlib
from pathlib import Path
from decoder import expected,canonical,filename,record
p=Path(__file__).resolve().parent
I={'nonce':'60fd2da461f6404ea93e47eb59d6831a','pid':12345,'view':'01234567-89ab-cdef-0123-456789abcdef'}
base=expected(I,'appear',0,0);rows=[]
def add(name,raw,admit=False):
 try:record(raw,filename(base),I,'appear',0,0);passed=True
 except ValueError:passed=False
 if passed!=admit:raise ValueError('Unexpected model admission: '+name)
 rows.append({'name':name,'raw_base64':base64.b64encode(raw).decode(),'sha256':hashlib.sha256(raw).hexdigest(),'expected_admission':admit})
add('literal-positive',b'{"count":0,"event":"appear","nonce":"60fd2da461f6404ea93e47eb59d6831a","pid":12345,"schema":1,"sequence":0,"view":"01234567-89ab-cdef-0123-456789abcdef"}\n',True)
for key,value in [('count',1),('event','increment'),('nonce','f'*32),('pid',12346),('schema',2),('sequence',1),('view','ffffffff-ffff-ffff-ffff-ffffffffffff'),('count',False),('pid',True)]:add('canonical-mutant-'+key+'-'+str(value),canonical({**base,key:value}))
add('unknown-field',canonical({**base,'generation':1}));missing=dict(base);del missing['event'];add('missing-field',canonical(missing))
raw=canonical(base)
for name,bad in [('duplicate-key',raw.replace(b'"count":0',b'"count":0,"count":0')),('padding',raw+b' '),('missing-newline',raw[:-1]),('nul-tail',raw+b'\0'),('pretty-json',json.dumps(base).encode()+b'\n'),('nonascii',raw.replace(b'appear',b'\xc3\xa9')),('oversize',b'x'*513)]:add(name,bad)
(p/'model-cases.json').write_text(json.dumps({'tier':'synthetic only','identity':I,'cases':rows},indent=2)+'\n')
print(json.dumps({'synthetic_cases':len(rows),'rejected':sum(not x['expected_admission'] for x in rows),'source':'Python model; no native records'}))
