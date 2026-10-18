import hashlib,json,sys,copy,unittest
from pathlib import Path
from decoder import expected,canonical,filename,record
p=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def verify(data):
 need(data['ui_sessions']==0 and data['native_button_input'] is False,'scope')
 need([x['name'] for x in data['controls']]==['positive','duplicate'],'controls')
 total=0
 for x in data['controls']:
  positive=x['name']=='positive';wait=x['actual_wait']
  need(wait['exit_code']==(0 if positive else 1) and wait['execution']==('success' if positive else 'failed'),'actual wait')
  identity=x['identity'];raw={k:bytes.fromhex(v) for k,v in x['files_hex'].items()}
  wants=[expected(identity,'appear' if i==0 else 'increment',i,i) for i in range(4 if positive else 1)]
  names={filename(v) for v in wants}
  if not positive:names.add('.pending-'+filename(wants[0]))
  need(set(raw)==names,'namespace')
  for v in wants:record(raw[filename(v)],filename(v),identity,v['event'],v['sequence'],v['count'])
  if not positive:
   conflict=expected(identity,'increment',0,1)
   need(raw['.pending-'+filename(conflict)]==canonical(conflict),'conflict bytes')
  count=sum(map(len,raw.values()));need(count==x['bytes_compared'],'byte accounting');total+=count
 return total
class Faults(unittest.TestCase):
 def mutant(self,change):
  v=copy.deepcopy(data);change(v)
  with self.assertRaises((ValueError,KeyError)):verify(v)
 def test_nonzero_positive(self):self.mutant(lambda v:v['controls'][0]['actual_wait'].update(exit_code=1))
 def test_success_shaped_failure(self):self.mutant(lambda v:v['controls'][1]['actual_wait'].update(execution='success'))
 def test_missing_receipt(self):self.mutant(lambda v:v['controls'][0]['files_hex'].pop(next(iter(v['controls'][0]['files_hex']))))
 def test_trailing_byte(self):self.mutant(lambda v:v['controls'][0]['files_hex'].update({next(iter(v['controls'][0]['files_hex'])):next(iter(v['controls'][0]['files_hex'].values()))+'00'}))
 def test_pending_byte(self):self.mutant(lambda v:v['controls'][1]['files_hex'].update({k:s+'20' for k,s in v['controls'][1]['files_hex'].items() if k.startswith('.pending-')}))
 def test_pid_binding(self):self.mutant(lambda v:v['controls'][0]['identity'].update(pid=v['controls'][0]['identity']['pid']+1))
if __name__=='__main__':
 seal=json.loads((p/'seal.json').read_text())
 for n,h in seal['files'].items():need(not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
 data=json.loads((p/'runtime-result.json').read_text());total=verify(data)
 for x in data['controls']:
  run=json.loads((p/('runtime-'+x['name'])/'execution.json').read_text());need(run['result']==x['actual_wait'],'wait linkage')
  starts=[e for e in run['events'] if e['event']=='process_started'];need(len(starts)==1 and starts[0]['pid']==x['identity']['pid'],'parent PID linkage')
  need(any(e['event']=='owned_descendant_cleanup' for e in run['events']),'cleanup')
  for name,raw in x['files_hex'].items():need((p/'native-receipts'/x['name']/name).read_bytes()==bytes.fromhex(raw),'retained bytes')
 for n in ['cli-compile','ui-typecheck']:
  run=json.loads((p/n/'execution.json').read_text());need(run['result']['execution']=='success' and run['result']['exit_code']==0,'compile wait')
  need(len([e for e in run['events'] if e['event']=='process_started'])==1 and any(e['event']=='owned_descendant_cleanup' for e in run['events']),'compile lifecycle')
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Faults);result=unittest.TextTestRunner().run(suite)
 if not result.wasSuccessful():sys.exit(1)
 print(json.dumps({'verified':True,'files':len(seal['files']),'native_receipt_bytes':total,'fault_methods':6,'UI_input_qualified':False}))
