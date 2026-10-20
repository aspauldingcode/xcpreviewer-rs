from pathlib import Path
import json,copy,sys

def check(a,b):
 for row,mode in [(a,'endpoint'),(b,'connection')]:
  assert row['mode']==mode and row['is_null_endpoint'] and not row['activate_invoked']
  assert row['service']=='owned.null.service'and row['instance']=='owned.null.instance'and row['endpoint_class']=='BSServiceConnectionEndpoint'
  assert row['remote_target_nil_before_activation'] and row['interposed_mach_calls']==len(row['trace'])<256
  assert row['interposed_mach_sends']==sum(bool(t['options']&1)for t in row['trace'])
 assert a['interposed_mach_calls']==0 and not a['invalidate_invoked']
 assert b['connection_class']=='BSServiceInitiatingConnection'and b['valid_before_activation']and b['invalidate_invoked']and b['interposed_mach_sends']>0
 return True
def verify(folder):
 a=json.loads((folder/'endpoint.json').read_text());b=json.loads((folder/'connection.json').read_text());check(a,b);n=0
 for field,value in [('valid_before_activation',False),('remote_target_nil_before_activation',False),('activate_invoked',True),('invalidate_invoked',False),('connection_class','Fake'),('interposed_mach_sends',0)]:
  bad=copy.deepcopy(b);bad[field]=value
  try:check(a,bad)
  except AssertionError:n+=1
  else:raise AssertionError('accepted mutated receipt')
 return {'successful_native_cases':2,'receipt_mutations_rejected':n,'endpoint_interposed_calls':0,'constructor_interposed_calls':b['interposed_mach_calls'],'constructor_interposed_sends':b['interposed_mach_sends'],'valid_before_activation':True,'remote_target_nil_before_activation':True,'owned_invalidate_invoked':True,'no_ipc_claim':False,'workspace_delivery_observed':False,'settlement_proven':False}
if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1])),indent=2))
