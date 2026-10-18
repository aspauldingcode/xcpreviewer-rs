import hashlib,json,sys,copy,unittest
from pathlib import Path
from decoder import expected,canonical,filename,record
p=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def verify(data):
 need(data['runtime_control_accepted'] is False and data['duplicate_started'] is False and data['native_button_input'] is False and data['ui_sessions']==0,'scope')
 wait=data['actual_wait'];need(wait['exit_code']==0 and wait['execution']=='failed','retained failed gate')
 identity=data['identity'];raw={k:bytes.fromhex(v) for k,v in data['files_hex'].items()}
 wants=[expected(identity,'appear' if i==0 else 'increment',i,i) for i in range(4)]
 need(set(raw)=={filename(v) for v in wants},'namespace')
 for v in wants:record(raw[filename(v)],filename(v),identity,v['event'],v['sequence'],v['count'])
 total=sum(map(len,raw.values()));need(total==data['bytes_compared'],'byte accounting');return total
class Faults(unittest.TestCase):
 def mutant(self,change):
  v=copy.deepcopy(data);change(v)
  with self.assertRaises((ValueError,KeyError)):verify(v)
 def test_success_promotion(self):self.mutant(lambda v:v.update(runtime_control_accepted=True))
 def test_success_shaped_wait(self):self.mutant(lambda v:v['actual_wait'].update(execution='success'))
 def test_missing_receipt(self):self.mutant(lambda v:v['files_hex'].pop(next(iter(v['files_hex']))))
 def test_trailing_byte(self):self.mutant(lambda v:v['files_hex'].update({next(iter(v['files_hex'])):next(iter(v['files_hex'].values()))+'00'}))
 def test_pid_binding(self):self.mutant(lambda v:v['identity'].update(pid=v['identity']['pid']+1))
 def test_duplicate_claim(self):self.mutant(lambda v:v.update(duplicate_started=True))
if __name__=='__main__':
 seal=json.loads((p/'seal.json').read_text())
 for n,h in seal['files'].items():need(not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
 data=json.loads((p/'assessment.json').read_text());total=verify(data)
 run=json.loads((p/'runtime-positive/execution.json').read_text());need(run['result']==data['actual_wait'],'wait linkage')
 starts=[e for e in run['events'] if e['event']=='process_started'];need(len(starts)==1 and starts[0]['pid']==data['identity']['pid'],'parent PID linkage')
 need(any(e['event']=='owned_descendant_cleanup' for e in run['events']),'cleanup')
 need((p/'runtime-positive/stderr.txt').read_text()=='OSError: Cannot observe a live owned root','observer failure')
 for name,raw in data['files_hex'].items():need((p/'native-receipts/positive'/name).read_bytes()==bytes.fromhex(raw),'retained bytes')
 for n in ['cli-compile','ui-typecheck']:
  run=json.loads((p/n/'execution.json').read_text());need(run['result']['execution']=='success' and run['result']['exit_code']==0,'compile wait')
  need(len([e for e in run['events'] if e['event']=='process_started'])==1 and any(e['event']=='owned_descendant_cleanup' for e in run['events']),'compile lifecycle')
 for n in ['runtime-result.json','runtime-duplicate','native-receipts/duplicate']:need(not(p/n).exists(),'unexecuted duplicate/result')
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Faults);result=unittest.TextTestRunner().run(suite)
 if not result.wasSuccessful():sys.exit(1)
 print(json.dumps({'verified':True,'files':len(seal['files']),'native_receipt_bytes':total,'fault_methods':6,'runtime_control_accepted':False,'UI_input_qualified':False}))
