"""Isolated native research validator. Not a portable event decoder or dispatcher.

Only the owned worker decodes data. A crash, timeout, invalid output or rejection
is a validation failure. Child exit is not a general target-settlement receipt;
this worker never posts events and never connects to an application.
"""
from pathlib import Path
import json,subprocess,resource

def validate(worker,source,timeout=2):
    def limits():
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    try:
        p=subprocess.run([str(Path(worker).resolve()),str(Path(source).resolve())],capture_output=True,timeout=timeout,preexec_fn=limits)
    except subprocess.TimeoutExpired:
        return {'accepted':False,'status':'timeout'}
    if p.returncode:
        return {'accepted':False,'status':'crash' if p.returncode<0 else 'worker_error','returncode':p.returncode}
    try:
        r=json.loads(p.stdout)
        if not isinstance(r,dict) or type(r.get('accepted')) is not bool:raise ValueError('response')
        if r['accepted'] and any(type(r.get(k)) is not int for k in ['type','timestamp','flags']):raise ValueError('fields')
    except (ValueError,TypeError):
        return {'accepted':False,'status':'invalid_response'}
    return {**r,'status':'accepted' if r['accepted'] else 'rejected'}

if __name__=='__main__':
    import sys
    print(json.dumps(validate(sys.argv[1],sys.argv[2])))
