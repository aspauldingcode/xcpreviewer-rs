"""Synthetic checks that failed UI qualification cannot be upgraded to success."""
from pathlib import Path
import json,tempfile
from verify import verify
root=Path(__file__).resolve().parent;names=['observations.json','postflight.json','crash-summary.json','new-target.json','launchservices-recovery.json'];results=[]
for case in ['false-interaction-acceptance','wrong-click-receipt','changed-source','false-crash-causation']:
    values={n:json.loads((root/n).read_text()) for n in names}
    if case=='false-interaction-acceptance':values['observations.json']['interaction_exercised']=True
    elif case=='wrong-click-receipt':values['observations.json']['visual_action']['result']['detail']='clicked 1116,136 in Xcode'
    elif case=='changed-source':values['postflight.json']['source_sha256']='changed'
    elif case=='false-crash-causation':values['crash-summary.json']['causation_verified']=True
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)
        for name,value in values.items():(p/name).write_text(json.dumps(value))
        try:verify(p)
        except (AssertionError,KeyError,StopIteration):results.append({'case':case,'rejected':True})
        else:raise AssertionError('False evidence accepted: '+case)
print(json.dumps({'kind':'synthetic-failure-record-controls','results':results},indent=2))
