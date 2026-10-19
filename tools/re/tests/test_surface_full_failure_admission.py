"""Offline R1 admission counterexamples; never runs the native fixture."""
import hashlib,importlib.util,json,shutil,sys,tempfile,unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
FAULTS=['positive','compile_bool','compile_float','wait_bool','wait_float','sender_float','receiver_float','manifest_bytes_float','duplicate_manifest','duplicate_compile','duplicate_wait','duplicate_row','duplicate_environment','duplicate_rea','duplicate_prior','nonfinite_nan','nonfinite_infinity','nonfinite_overflow','exit','timeout','completion','audit','rights','cleanup','peer','signal','allocation','active','padding','tail']
def reseal(e):
 (e/'manifest.json').write_text(json.dumps({'files':{str(p.relative_to(e)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}}))
def inject(p,key,raw):p.write_text('{'+json.dumps(key)+':'+raw+','+p.read_text().lstrip()[1:])
def case(e,source,fault):
 shutil.copytree(source,e);p=e/'wait.json';d=json.loads(p.read_text());rows=[json.loads(x) for x in d['stdout'].splitlines()]
 if fault in ['compile_bool','compile_float']:
  q=e/'compile.json';v=json.loads(q.read_text());v['code']=False if fault.endswith('bool') else 0.0;q.write_text(json.dumps(v))
 elif fault in ['wait_bool','wait_float']:d['code']=False if fault.endswith('bool') else 0.0
 elif fault=='sender_float':
  for row in rows:row['sender_pid']=float(row['sender_pid'])
 elif fault=='receiver_float':
  for row in rows:row['receiver_pid']=float(row['receiver_pid'])
 elif fault=='exit':d['code']=43
 elif fault=='timeout':d['timeout']=True
 elif fault=='completion':rows[1]['completion_accepted']=True
 elif fault=='audit':rows[1]['audit_peer_verified']=False
 elif fault=='rights':rows[1]['local_resource_refs_retained']=0
 elif fault=='cleanup':rows[1]['local_resource_name_removed']=False
 elif fault=='peer':rows[1]['receiver_pid']=rows[0]['receiver_pid']
 elif fault=='signal':rows[1]['peer_signal']=0
 elif fault=='allocation':rows[1]['allocation_bytes']=1152
 elif fault in ['active','padding','tail']:
  q=e/'before-ack/retained.bin';b=bytearray(q.read_bytes());b[{'active':0,'padding':68,'tail':16383}[fault]]^=1;q.write_bytes(b)
 d['stdout']=''.join(json.dumps(x)+'\n' for x in rows);p.write_text(json.dumps(d))
 if fault=='duplicate_compile':inject(e/'compile.json','code','9')
 elif fault=='duplicate_wait':inject(p,'code','9')
 elif fault=='duplicate_row':
  d=json.loads(p.read_text());lines=d['stdout'].splitlines();lines[0]='{"completion_accepted":true,'+lines[0].lstrip()[1:];d['stdout']='\n'.join(lines)+'\n';p.write_text(json.dumps(d))
 elif fault=='duplicate_environment':inject(e/'environment.json','helper_sha256','"contradictory"')
 elif fault=='duplicate_rea':inject(e/'rea.json','open','null')
 elif fault=='duplicate_prior':
  q=e/'prior-verification.json';v=q.read_text();q.write_text(v.replace('"valid": true','"valid":false,"valid": true',1))
 elif fault.startswith('nonfinite_'):inject(e/'environment.json','unused_debug',{'nonfinite_nan':'NaN','nonfinite_infinity':'Infinity','nonfinite_overflow':'1e999'}[fault])
 reseal(e)
 if fault=='duplicate_manifest':inject(e/'manifest.json','files','{}')
 elif fault=='manifest_bytes_float':
  q=e/'manifest.json';v=json.loads(q.read_text());n=next(iter(v['files']));v['files'][n]['bytes']=float(v['files'][n]['bytes']);q.write_text(json.dumps(v))
def run(verifier,source):
 spec=importlib.util.spec_from_file_location('r1reader',verifier);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);rows=[]
 for fault in FAULTS:
  with tempfile.TemporaryDirectory(prefix='r1-full-reader-') as t:
   e=Path(t)/'e';case(e,source,fault)
   try:result=m.verify(e);accepted=True;error=None
   except (ValueError,AssertionError,KeyError,TypeError) as ex:accepted=False;result=None;error=type(ex).__name__
   rows.append({'fault':fault,'accepted':accepted,'error':error,'result':result})
 return {'optimized':not __debug__,'cases':rows,'native_execution':False}
class FullFailureAdmissionTests(unittest.TestCase):
 def test_counterexamples(self):
  result=run(Path(__file__).with_name('verify_surface_full_failure.py'),ROOT/'research/evidence/surface-full-failure-2026-10-11')
  for row in result['cases']:
   with self.subTest(fault=row['fault']):self.assertIs(row['accepted'],row['fault']=='positive')
 @unittest.skipIf(not __debug__,'Already optimized')
 def test_optimized(self):
  z=subprocess.run([sys.executable,'-O','-B',__file__],capture_output=True,text=True,timeout=25);self.assertEqual(z.returncode,0,z.stdout+z.stderr)
if __name__=='__main__':unittest.main()
