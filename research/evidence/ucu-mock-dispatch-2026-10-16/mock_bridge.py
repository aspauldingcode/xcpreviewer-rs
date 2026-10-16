#!/usr/bin/python3 -I
"""Controlled protocol peer: no AX, AppKit, browser or UI imports/actions."""
import json,os,sys
from pathlib import Path
log=Path(os.environ['ROUTING_RECORD'])
with log.open('x') as f:
    for line in sys.stdin:
        q=json.loads(line)
        f.write(json.dumps({'pid':os.getpid(),'request':q})+'\n');f.flush()
        if q.get('method')!='act':
            reply={'id':q['id'],'ok':False,'error':'Mock rejects non-act methods'}
        elif q.get('op')=='PRESS':
            reply={'id':q['id'],'ok':False,'acted':False,'error':'MOCK: element offers CLICK but no AXPress'}
        elif q.get('op')=='CLICK':
            reply={'id':q['id'],'ok':True,'result':{'mock_only':True,'forwarded':'CLICK'}}
        else:
            reply={'id':q['id'],'ok':False,'error':'Unexpected operation'}
        print(json.dumps(reply),flush=True)
