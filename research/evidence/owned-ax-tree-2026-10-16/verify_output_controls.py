import json,re,hashlib
from pathlib import Path
from admit import need,integer,receipt

def verify(root):
 root=Path(root);compile=json.loads((root/'compile-record.json').read_text());out={}
 for name,code,message in [('output-valid',0,None),('output-invalid',81,'owned_output_serialization_failed'),('output-large',82,'owned_output_limit'),('output-write',83,'owned_output_write_failed')]:
  row=json.loads((root/(name+'-record.json')).read_text());r=row['record'];p=r['report'];need(row['args']==['--output-control',name] and row['binary_sha256']==compile['binary_sha256'] and row['source_sha256']==compile['source_sha256'])
  need(integer(p['target_code'],code) and p['failure'] is None and p['drained'] is True and integer(p['remaining_observed'],0) and r['emergencyClosed'] is False and r['privateAbortRequested'] is False)
  if code==0:need(receipt(row)['status']=='owned_output_control')
  else:
   need(type(row['error']) is str and integer(r['stdoutBytes'],0) and r['stdout']=='' and r['stdoutSha256']==hashlib.sha256(b'').hexdigest() and message in r['stderr'])
   markers=re.findall(r'^owned_tree_pid:([1-9][0-9]*)$',r['stderr'],re.M);need(len(markers)==1 and 1<int(markers[0])<=2147483647)
  out[name]={'actual_target_code':code,'scoped_drained':True,'expected_failure_retained':code!=0}
 return out
if __name__=='__main__':
 p=Path(__file__).parent;v=verify(p);(p/'output-controls-admission.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
