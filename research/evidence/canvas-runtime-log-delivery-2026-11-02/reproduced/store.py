"""Read bounded unified-log records for the exact owned control PIDs; publish selected messages only."""
from pathlib import Path
import argparse,subprocess,json
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();root=a.directory
for label,filename in [('untraced','native-policy-log-unfulfilled.result.json'),('gated-untraced','gated-policy-log-unfulfilled.result.json'),('traced','policy-log-unfulfilled.trace-result.json')]:
 pid=json.loads((root/filename).read_text())['pid']
 try:
  result=subprocess.run(['/usr/bin/log','show','--last','3m','--style','json','--predicate',f'processIdentifier == {pid}'],capture_output=True,timeout=8)
  rows=json.loads(result.stdout) if result.returncode==0 else []
  selected=[{'pid':r.get('processID'),'message':r.get('eventMessage'),'sender':r.get('senderImagePath'),'subsystem':r.get('subsystem'),'category':r.get('category')} for r in rows if r.get('processID')==pid and (r.get('eventMessage','').startswith('FulfillOnce failure: owned-policy') or r.get('eventMessage')=='<compose failure [missing precomposed log]>')]
  summary={'pid':pid,'code':result.returncode,'timeout':False,'record_count':len(rows),'selected':selected,'raw_records_published':False}
 except subprocess.TimeoutExpired:summary={'pid':pid,'timeout':True,'selected':[],'raw_records_published':False}
 (root/(label+'-store.json')).write_text(json.dumps(summary,indent=2)+'\n');print(label,json.dumps(summary))
