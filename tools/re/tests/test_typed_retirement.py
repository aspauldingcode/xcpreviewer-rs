import hashlib,json,shutil,tempfile,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
from reloop.processretirement import RetirementObserver
from verify_typed_retirement import verify
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'research/evidence/typed-retirement-2026-10-11'
class TypedRetirementTests(unittest.TestCase):
 def test_seal_reader_sources(self):
  self.assertEqual(hashlib.sha256((E/'manifest.json').read_bytes()).hexdigest(),SEAL);self.assertFalse(verify(E)['unreaped_retirement_qualified'])
  for source,name in [('tools/re/native/OwnedProcessRetirement.c','OwnedProcessRetirement.c'),('tools/re/reloop/processretirement.py','processretirement-after.py'),('tools/re/fixtures/OwnedRetirementVisibility/main.c','owner-query/main.c')]:self.assertEqual((ROOT/source).read_bytes(),(E/name).read_bytes())
 def test_resealed_faults(self):
  for fault in ['exit','waitid','signal','typed-zombie','typed-birth','wrong-birth','owner-bytes','owner-status','byte','helper','qualified','budget','missing-phase','rea']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    e=Path(tmp)/'e';shutil.copytree(E,e)
    if fault in ['exit','waitid','signal']:
     p=e/'result.json';d=json.loads(p.read_text())
     if fault=='exit':d['root_exit_code']=1
     elif fault=='waitid':d['unreaped']['status']=0
     else:d['signals']=[9]
    elif fault in ['typed-zombie','typed-birth','missing-phase','owner-bytes','owner-status']:
     p=e/('owner-query/samples.json' if fault.startswith('owner-') else 'samples.json');d=json.loads(p.read_text());child=next(iter(d[1]['typed']))
     if fault=='typed-zombie':d[1]['typed'][child].update(status='retired',observed_birth=d[1]['typed'][child]['expected_birth'])
     elif fault=='typed-birth':d[0]['typed'][child]['observed_birth'][0]+=1
     elif fault=='owner-bytes':d[1]['owner']['query']['bytes']=136
     elif fault=='owner-status':d[0]['owner']['query']['state']=5
     else:d.pop()
    elif fault=='wrong-birth':p=e/'wrong-birth.json';d=json.loads(p.read_text());next(iter(d['rows'].values()))['status']='live'
    elif fault=='byte':p=e/'owner-query/child.bin';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);d=None
    elif fault=='helper':p=e/'environment.json';d=json.loads(p.read_text());d['typed_helper_sha256']='0'*64
    elif fault=='rea':p=e/'rea-status.json';d=json.loads(p.read_text());d['target']['architecture']='x86_64'
    else:
     p=e/'retained-failure.json';d=json.loads(p.read_text());d['native_retirement_qualified' if fault=='qualified' else 'native_subprocesses']=True if fault=='qualified' else 10
    if d is not None:p.write_text(json.dumps(d))
    (e/'manifest.json').write_text(json.dumps({'files':{str(q.relative_to(e)):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in e.rglob('*') if q.is_file() and q!=e/'manifest.json'}}))
    with self.assertRaises(AssertionError):verify(e)
 def test_explicit_adapter_status_contract(self):
  observer=RetirementObserver('/owned/helper');known={10:(1,2,'/owned/old-path')}
  for status,birth in [('live',[1,2]),('retired',[1,2]),('reused',[3,2]),('unavailable',None)]:
   data=[{'pid':10,'expected_birth':[1,2],'observed_birth':birth,'status':status}]
   with patch('reloop.processretirement.subprocess.run',return_value=subprocess.CompletedProcess([],0,json.dumps(data).encode(),b'')) as run:
    self.assertEqual(observer.snapshot(known)[10]['status'],status);self.assertEqual(run.call_args.kwargs['timeout'],2);self.assertTrue(run.call_args.kwargs['check']);self.assertEqual(run.call_args.args[0],['/owned/helper','10:1:2'])
 def test_malformed_output_and_deadline_fail_closed(self):
  observer=RetirementObserver('/owned/helper');known={10:(1,2,'/owned')};row={'pid':10,'expected_birth':[1,2],'observed_birth':[1,2],'status':'retired'}
  cases=[[],[row,row],[dict(row,pid=11)],[dict(row,expected_birth=[True,2])],[dict(row,observed_birth=[True,2])],[dict(row,status='unavailable')],[dict(row,status='reused')],[dict(row,status='unknown')],[dict(row,observed_birth=None)]]
  for rows in cases:
   with patch('reloop.processretirement.subprocess.run',return_value=subprocess.CompletedProcess([],0,json.dumps(rows).encode(),b'')):
    with self.assertRaises(ValueError):observer.snapshot(known)
  with patch('reloop.processretirement.subprocess.run',side_effect=subprocess.TimeoutExpired(['owned'],2)):
   with self.assertRaises(subprocess.TimeoutExpired):observer.snapshot(known)
 def test_invalid_known_identity_prevents_launch(self):
  observer=RetirementObserver('/owned/helper')
  for known in [{},{True:(1,2,'/owned')},{10:(True,2,'/owned')},{10:(-1,2,'/owned')},{10:(1,2,'relative')},{n:(1,2,'/owned') for n in range(1,1026)}]:
   with patch('reloop.processretirement.subprocess.run') as run:
    with self.assertRaises(ValueError):observer.snapshot(known)
    run.assert_not_called()
SEAL='6001d8cf10daf5b8bff35359dee99e4eb9152ed8f0f22f16a736911001f46e35'
