from pathlib import Path
import json,copy,sys,importlib.util
w=Path(__file__).parent;spec=importlib.util.spec_from_file_location('lifetime',w/'verify-lifetime.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
BASE=0x1a82b6000
EXPECTED_OFFSETS=[a-BASE for a in [0x1a831f834,0x1a831f4ec,0x1a830eb2c]]
INFO={'BSErrorCodeDescription':'OperationFailed','NSLocalizedFailureReason':'XPC error received on message reply handler'}
def check(d,mode):
 old.check(d,mode)
 assert d['factory_types']=='@40@0:8@16q24@32' and d['factory_restored'] is True
 assert d['factory_hits']==(1 if mode=='withheld'else 0)
 if mode=='withheld':
  assert d['factory_user_info']==INFO
  offsets=[x['offset']for x in d['factory_stack']if x['image']=='/System/Library/PrivateFrameworks/BoardServices.framework/Versions/A/BoardServices'];assert offsets[:3]==EXPECTED_OFFSETS
 else:assert d['factory_user_info']=={}and d['factory_stack']==[]
if __name__=='__main__':
 folder=Path(sys.argv[1]);n=0;cases=[]
 for mode in ['delivered','withheld','late-after-invalidate']:
  d=json.load(open(folder/(mode+'.json')));check(d,mode)
  for key in ['factory_hits','factory_restored','factory_types','factory_user_info','factory_stack']:
   bad=copy.deepcopy(d)
   if key=='factory_hits':bad[key]+=1
   elif key=='factory_restored':bad[key]=False
   elif key=='factory_types':bad[key]='incorrect'
   elif key=='factory_user_info':bad[key]={'mutant':'x'}
   else:bad[key]=[]if mode=='withheld'else[{'image':'mutant','offset':1}]
   try:check(bad,mode)
   except AssertionError:n+=1
   else:raise AssertionError('accepted constructor evidence mutation')
  if mode=='withheld':
   for i in range(3):
    bad=copy.deepcopy(d);j=[j for j,x in enumerate(bad['factory_stack'])if 'BoardServices' in x['image']][i];bad['factory_stack'][j]['offset']+=4
    try:check(bad,mode)
    except AssertionError:n+=1
    else:raise AssertionError('accepted native callsite offset mutation')
  cases.append({'mode':mode,'factory_hits':d['factory_hits'],'hook_restored':True,'native_error_info_equal':mode=='withheld','native_source_chain_offsets':EXPECTED_OFFSETS if mode=='withheld'else[]})
 print(json.dumps({'cases':cases,'constructor_mutations_rejected':n,'actual_native_error_info':INFO,'private_callable_ABI_used':False,'target_operation_settlement':False},indent=2))
