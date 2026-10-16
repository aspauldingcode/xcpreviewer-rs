"""Pinned local source discriminator; no native tools, UI actions or binary inference."""
import hashlib,json
from pathlib import Path

def inspect(data,expected):
    if hashlib.sha256(data).hexdigest()!=expected:
        raise ValueError('Source pin mismatch')
    text=data.decode('utf-8')
    arm='"press" | "click" | "PRESS" => "PRESS",'
    if text.count(arm)!=1:
        raise ValueError('Source arm missing or ambiguous')
    return {'input':'click','forwarded_operation':'PRESS','requested_pointer_click_preserved':False,'grade':'pinned-source-only'}

if __name__=='__main__':
    findings=json.loads(Path(__file__).with_name('source-findings.json').read_text())
    checks=[]
    for source in findings['sources']:
        data=Path(source['path']).read_bytes()
        if len(data)!=source['bytes'] or hashlib.sha256(data).hexdigest()!=source['sha256']:
            raise ValueError('Source identity changed')
        checks.append({'path':source['path'],'sha256':source['sha256'],'matched':True})
    source=findings['sources'][0];data=Path(source['path']).read_bytes()
    result=inspect(data,source['sha256'])
    try:inspect(data+b'\n',source['sha256'])
    except ValueError:negative=True
    else:raise RuntimeError('Altered source falsely accepted')
    print(json.dumps({'sources':checks,'dispatch':result,'altered_byte_rejected':negative,'runtime_attribution':False},indent=2))
