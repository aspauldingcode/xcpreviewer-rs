"""Content-addressed, bounded MCP responses; bulk content stays local."""
import json
import re
from reloop.core import atomic, digest, load
from reloop.evidence import compact


def bounded(controller,value,maximum=6000):
    original=json.dumps(value,ensure_ascii=False)
    if len(original)<=maximum:return value
    text=json.dumps(compact(value),ensure_ascii=False)
    directory=controller.state/'responses';directory.mkdir(exist_ok=True)
    # Store full JSON, not the compacted representation. Pages never silently lose evidence.
    from reloop.core import canonical_hash
    key=canonical_hash(value);path=directory/(key+'.json')
    if not path.exists():atomic(path,value)
    return {'response_id':key,'sha256':digest(path),'full_chars':len(path.read_text()),
            'preview':text[:maximum-500],'next_offset':0,
            'note':'Bounded preview. Use re_response for exact pages; preview may omit blobs/arrays. Character count is measured; tokens depend on tokenizer.'}


def page(controller,key,offset=0,chars=6000):
    if not isinstance(key,str) or not re.fullmatch('[0-9a-f]{64}',key):raise ValueError('Invalid response ID')
    if type(offset) is not int or offset<0 or type(chars) is not int or not 1<=chars<=12000:raise ValueError('Invalid response bounds')
    path=controller.state/'responses'/(key+'.json')
    value=load(path)
    from reloop.core import canonical_hash
    if value is None or canonical_hash(value)!=key:raise RuntimeError('Response missing or changed')
    text=path.read_text()
    return {'response_id':key,'offset':offset,'text':text[offset:offset+chars],
            'next_offset':offset+chars if offset+chars<len(text) else None,'sha256':digest(path)}
