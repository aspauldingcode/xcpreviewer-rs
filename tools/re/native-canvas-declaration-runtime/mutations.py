"""Synthetic failure controls for retained artifacts; never drives native UI."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,tempfile,shutil,importlib.util
r=Path(sys.argv[1]);spec=importlib.util.spec_from_file_location('reader',Path(__file__).with_name('verify.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
results=[]
for mode in ['missing-provider-call','wrong-provider-registry-order','missing-content-return','missing-state-entry','overclaimed-resource-release','tab-not-added','tab-not-removed','source-not-restored']:
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/'e';shutil.copytree(r,p)
  if mode in ['missing-provider-call','wrong-provider-registry-order','missing-content-return','missing-state-entry']:
   ep=p/'run1/events.jsonl';rows=[json.loads(x) for x in ep.read_text().splitlines()]
   def payload(x):return x.get('message',{}).get('payload',{})
   def first(fn,event):return next(x for x in rows if payload(x).get('function')==fn and payload(x).get('event')==event)
   if mode=='missing-provider-call':
    ident=payload(first('providers','enter'))['id'];rows=[x for x in rows if payload(x).get('id')!=ident]
   elif mode=='wrong-provider-registry-order':
    a=rows.index(first('providers','enter'));b=rows.index(first('registries','enter'));rows[a],rows[b]=rows[b],rows[a]
   else:rows.remove(first('canvas-content-destroy','return') if mode=='missing-content-return' else first('preview-state-destroy','enter'))
   for i,x in enumerate(rows):x['time_ns']=1000+i
   ep.write_text(''.join(json.dumps(x)+'\n' for x in rows))
  elif mode=='overclaimed-resource-release':
   op=p/'observations.json';o=json.loads(op.read_text());o['native_resource_release_verified']=True;op.write_text(json.dumps(o))
  elif mode=='tab-not-added':
   ap=p/'run1/added-ready-ax.txt';ap.write_text('\n'.join(x for x in ap.read_text().splitlines() if not ('text Runtime addition' in x)))
  elif mode=='tab-not-removed':
   ap=p/'no-hooks/restored-settled-ax.txt';ap.write_text(ap.read_text()+'\n    999 text Runtime addition\n')
  else:
   ep=p/'no-hooks/events.jsonl';rows=[json.loads(x) for x in ep.read_text().splitlines()];rows[-1]['source_restored']=False;ep.write_text(''.join(json.dumps(x)+'\n' for x in rows))
  try:m.verify(p)
  except (AssertionError,KeyError,ValueError):results.append({'synthetic_mutation':mode,'rejected':True})
  else:raise AssertionError(mode)
print(json.dumps(results,indent=2))
