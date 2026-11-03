"""Synthetic retained-trace controls, not additional native execution."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,tempfile,shutil,importlib.util
r=Path(sys.argv[1]);spec=importlib.util.spec_from_file_location('reader',Path(__file__).with_name('verify.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
results=[]
for fault in ['wrong-owner','point-after-return','missing-owner-return','wrong-thread','interior-as-function','source-not-restored','overclaimed-resource-release','invalid-sampling-limit']:
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/'e';shutil.copytree(r,p)
  if fault in ['wrong-owner','point-after-return','missing-owner-return','wrong-thread','invalid-sampling-limit']:
   f=p/'sampled-post-ack/events.jsonl';rows=[json.loads(x) for x in f.read_text().splitlines()]
   def payload(x):return x.get('message',{}).get('payload',{})
   pt=next(x for x in rows if payload(x).get('event')=='point');ident=payload(pt)['owner_id']
   end=next(x for x in rows if payload(x).get('event')=='owner-return' and payload(x)['id']==ident)
   if fault=='wrong-owner':payload(pt)['owner_id']=999999
   elif fault=='point-after-return':rows.remove(pt);rows.insert(rows.index(end)+1,pt)
   elif fault=='missing-owner-return':rows.remove(end)
   elif fault=='wrong-thread':payload(pt)['thread']+=1
   else:next(payload(x) for x in rows if payload(x).get('event')=='hooks-ready')['sampled_owner_limit_per_phase']=20000
   for i,x in enumerate(rows):x['time_ns']=1000+i
   f.write_text(''.join(json.dumps(x)+'\n' for x in rows))
  elif fault=='interior-as-function':
   f=p/'boundary-qualification.json';d=json.loads(f.read_text());d['state_location_kind']='function-entry';f.write_text(json.dumps(d))
  elif fault=='source-not-restored':
   f=p/'sampled-post-ack/events.jsonl';rows=[json.loads(x) for x in f.read_text().splitlines()];rows[-1]['source_restored']=False;f.write_text(''.join(json.dumps(x)+'\n' for x in rows))
  else:
   f=p/'final-controls.json';d=json.loads(f.read_text());d['native_object_release_verified']=True;f.write_text(json.dumps(d))
  try:m.verify(p)
  except (AssertionError,KeyError,ValueError):results.append({'synthetic_mutation':fault,'rejected':True})
  else:raise AssertionError(fault)
print(json.dumps(results,indent=2))
