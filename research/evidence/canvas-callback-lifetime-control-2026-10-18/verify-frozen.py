import json,hashlib,copy,unittest,sys
from pathlib import Path
from decoder import expected,filename,canonical,record
p=Path(__file__).resolve().parent
def need(x,m):
 if not x:raise ValueError(m)
def verify(v):
 need(v['UI_input_qualified'] is False and v['deadline_closed'] is True,'scope')
 need([x['name'] for x in v['controls']]==['positive','duplicate'],'controls')
 total=0
 for x in v['controls']:
  positive=x['name']=='positive';report=x['report'];run=x['execution'];wait=run['result'];ident=x['identity']
  need(type(wait['exit_code']) is int and type(report['child_wait']) is int,'integer wait codes')
  need(all(type(z) is int and 1<z<2**31 for z in [report['wrapper_pid'],report['child_pid'],ident['pid']]),'integer PID fields')
  need(wait['execution']=='success' and wait['exit_code']==0,'wrapper wait')
  need(report['timed_out'] is False and report['child_wait']==(0 if positive else 1),'child wait')
  starts=[e for e in run['events'] if e['event']=='process_started']
  need(len(starts)==1 and type(starts[0]['pid']) is int and starts[0]['pid']==report['wrapper_pid'] and report['child_pid']==ident['pid'] and report['child_pid']!=report['wrapper_pid'],'PID linkage')
  need(any(e['event']=='owned_descendant_cleanup' for e in run['events']),'cleanup')
  raw={k:bytes.fromhex(s) for k,s in x['files_hex'].items()};wants=[expected(ident,'appear' if i==0 else 'increment',i,i) for i in range(4 if positive else 1)]
  names={filename(y) for y in wants}
  if not positive:names.add('.pending-'+filename(wants[0]))
  need(set(raw)==names,'namespace')
  for y in wants:record(raw[filename(y)],filename(y),ident,y['event'],y['sequence'],y['count'])
  if not positive:need(raw['.pending-'+filename(wants[0])]==canonical(expected(ident,'increment',0,1)),'conflict bytes')
  count=sum(map(len,raw.values()));need(count==x['bytes_compared'],'byte accounting');total+=count
 return total
class Faults(unittest.TestCase):
 def mutant(self,fn):
  v=copy.deepcopy(data);fn(v)
  with self.assertRaises((ValueError,KeyError)):verify(v)
 def test_child_success_shape(self):self.mutant(lambda v:v['controls'][1]['report'].update(child_wait=0))
 def test_wrapper_failure(self):self.mutant(lambda v:v['controls'][0]['execution']['result'].update(execution='failed'))
 def test_timeout(self):self.mutant(lambda v:v['controls'][0]['report'].update(timed_out=True))
 def test_trailing_byte(self):self.mutant(lambda v:v['controls'][0]['files_hex'].update({next(iter(v['controls'][0]['files_hex'])):next(iter(v['controls'][0]['files_hex'].values()))+'00'}))
 def test_missing_pending(self):self.mutant(lambda v:v['controls'][1]['files_hex'].pop(next(k for k in v['controls'][1]['files_hex'] if k.startswith('.pending-'))))
 def test_child_pid(self):self.mutant(lambda v:v['controls'][0]['report'].update(child_pid=v['controls'][0]['identity']['pid']+1))
 def test_overwritten_first(self):self.mutant(lambda v:v['controls'][1]['files_hex'].update({k.removeprefix('.pending-'):s for k,s in v['controls'][1]['files_hex'].items() if k.startswith('.pending-')}))
 def test_boolean_wait_codes(self):
  for index,key,value in [(0,'child_wait',False),(1,'child_wait',True)]:
   with self.subTest(index=index):self.mutant(lambda v:v['controls'][index]['report'].update({key:value}))
  self.mutant(lambda v:v['controls'][0]['execution']['result'].update(exit_code=False))
 def test_float_wait_codes(self):
  for index,code in [(0,0.0),(1,1.0)]:
   with self.subTest(index=index):self.mutant(lambda v:v['controls'][index]['report'].update(child_wait=code))
  self.mutant(lambda v:v['controls'][0]['execution']['result'].update(exit_code=0.0))
 def test_boolean_and_float_pids(self):
  for value in [True,False,34954.0]:
   for key in ['wrapper_pid','child_pid']:
    with self.subTest(value=value,key=key):self.mutant(lambda v:v['controls'][0]['report'].update({key:value}))
  self.mutant(lambda v:v['controls'][0]['identity'].update(pid=34960.0))
  self.mutant(lambda v:v['controls'][0]['execution']['events'][0].update(pid=34954.0))
if __name__=='__main__':
 seal=json.loads((p/'seal.json').read_text())
 for n,h in seal['files'].items():need(not(p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n)
 data=json.loads((p/'result.json').read_text());total=verify(data)
 for x in data['controls']:
  need(json.loads((p/x['name']/'stdout.txt').read_text())==x['report'],'retained report')
  need(json.loads((p/x['name']/'execution.json').read_text())==x['execution'],'retained wait')
  for n,s in x['files_hex'].items():need((p/'receipts'/x['name']/n).read_bytes()==bytes.fromhex(s),'retained bytes')
 result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Faults))
 if not result.wasSuccessful():sys.exit(1)
 print(json.dumps({'verified':True,'files':len(seal['files']),'receipt_bytes':total,'fault_methods':10,'UI_input_qualified':False}))
