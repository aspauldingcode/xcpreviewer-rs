from pathlib import Path
import subprocess,json,sys,hashlib
w=Path(__file__).parent;root=Path('/Users/8amps/xcpreviewer-rs');script=root/'tools/re/swiftui-preview/discover.py';rows=[]
for case in ['Controls','None','Invalid','Slow']:
 args=['python3',str(script),str(w/(case+'.swift'))]
 if case=='Slow':args+=['--runtime-seconds','0.1']
 r=subprocess.run(args,capture_output=True,timeout=90)
 (w/(case+'.stdout')).write_bytes(r.stdout);(w/(case+'.stderr')).write_bytes(r.stderr)
 if case in ['Controls','None']:
  assert r.returncode==0,r.stderr.decode();value=json.loads(r.stdout)
  if case=='Controls':
   assert [(x['line'],x['column'],x['display_name']) for x in value['previews']]==[(3,1,'Named control'),(5,1,None)]
   assert len({x['registry'] for x in value['previews']})==2
  else:assert value['previews']==[]
  rows.append({'case':case,'passed':True,'registries':len(value['previews'])})
 else:
  diagnostic='ThisOwnedTypeDoesNotExist' if case=='Invalid' else 'Owned process exceeded 0.1 seconds'
  assert r.returncode!=0 and diagnostic in r.stderr.decode() and r.stdout==b'',r.stderr.decode()
  rows.append({'case':case,'passed':True,'expected_failure':diagnostic})
(w/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
