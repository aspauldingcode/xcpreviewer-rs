"""Synthetic reader faults, not native executions."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,tempfile,shutil,importlib.util
r=Path(sys.argv[1]);spec=importlib.util.spec_from_file_location('reader',Path(__file__).with_name('verify.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);results=[]
for fault in ['fixture-failed','missing-load-rejection','class-guard-failed','missing-return','wrong-address-token','source-not-restored','claimed-ui-action','claimed-native-weak-lifetime']:
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/'e';shutil.copytree(r,p)
  if fault=='fixture-failed':
   f=p/'reproduction-build/controls.stdout';rows=[json.loads(x) for x in f.read_text().splitlines()];rows[0]['passed']=False;f.write_text(''.join(json.dumps(x)+'\n' for x in rows))
  elif fault in ['missing-load-rejection','class-guard-failed','missing-return','wrong-address-token','source-not-restored']:
   f=p/('load-blocked/events.jsonl' if fault=='missing-load-rejection' else 'file-a/events.jsonl');rows=[json.loads(x) for x in f.read_text().splitlines()]
   def payload(x):return x.get('message',{}).get('payload',{})
   if fault=='missing-load-rejection':
    for x in rows:
     if x.get('message',{}).get('type')=='error':x['message']['description']='unqualified error'
   elif fault=='class-guard-failed':next(payload(x) for x in rows if payload(x).get('event')=='editor-scene-observed')['expected_class']=False
   elif fault=='missing-return':rows.remove(next(x for x in rows if payload(x).get('event')=='method-return'))
   elif fault=='wrong-address-token':next(payload(x) for x in rows if payload(x).get('event')=='method-enter')['scene_id']=999
   else:rows[-1]['source_restored']=False
   for i,x in enumerate(rows):x['time_ns']=1000+i
   f.write_text(''.join(json.dumps(x)+'\n' for x in rows))
  else:
   f=p/('ui-blocked/ui-error.json' if fault=='claimed-ui-action' else 'final-controls.json');v=json.loads(f.read_text());v['ui_actions_executed' if fault=='claimed-ui-action' else 'native_weak_lifetime_verified']=True;f.write_text(json.dumps(v))
  try:m.verify(p)
  except (AssertionError,KeyError,ValueError):results.append({'synthetic_mutation':fault,'rejected':True})
  else:raise AssertionError(fault)
print(json.dumps(results,indent=2))
