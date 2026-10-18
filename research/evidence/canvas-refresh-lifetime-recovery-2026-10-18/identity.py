"""Read-only sampled full process identity; no liveness/reclamation inference."""
import datetime,hashlib,json,subprocess,time
from pathlib import Path
HELPER=Path('/Users/8amps/xcpreviewer-rs/research/build/libproc-observer/owned-process-snapshot')
HELPER_SHA='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5'
def need(ok,message):
 if not ok:raise ValueError(message)
def integer(v,low,high):return type(v) is int and low<=v<=high
def valid_identity(v):
 return (type(v) is list and len(v)==3 and integer(v[0],1,2**63-1) and integer(v[1],0,999999)
         and type(v[2]) is str and v[2].startswith('/') and '\x00' not in v[2])
def parse(raw,pid,expected=None):
 def pairs(items):
  out={}
  for key,value in items:need(key not in out,'duplicate key');out[key]=value
  return out
 need(integer(pid,2,2147483647),'PID domain')
 if expected is not None:need(valid_identity(expected),'expected identity')
 need(type(raw) is str and len(raw.encode())<=65536,'snapshot size')
 rows=json.loads(raw,object_pairs_hook=pairs);need(type(rows) is list and len(rows)<=256,'row count');seen=set();found=None
 for row in rows:
  need(type(row) is dict and set(row)=={'pid','parent','group','state','identity'},'row fields')
  need(integer(row['pid'],2,2147483647) and row['pid'] not in seen,'PID uniqueness');seen.add(row['pid'])
  need(integer(row['parent'],0,2147483647) and integer(row['group'],0,2147483647),'parent/group')
  need(row['state'] in ['L','Z'] and valid_identity(row['identity']),'identity')
  if row['pid']==pid:
   if expected is not None:need(row['identity']==expected,'retired identity returned')
   found=row
 return found

def snapshot(pid,expected=None):
 need(integer(pid,2,2147483647),'PID domain')
 if expected is not None:need(valid_identity(expected),'expected identity')
 need(HELPER.is_file() and not HELPER.is_symlink() and hashlib.sha256(HELPER.read_bytes()).hexdigest()==HELPER_SHA,'observer changed')
 selector=str(pid) if expected is None else '%d:%d:%d'%(pid,*expected[:2])
 record={'pid':pid,'expected_identity':expected,'selector':selector,'helper_sha256':HELPER_SHA,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()};start=time.monotonic()
 try:
  result=subprocess.run([str(HELPER),selector],capture_output=True,text=True,timeout=2)
  record.update(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
  need(result.returncode==0 and len(result.stderr.encode())<=4096,'helper failed')
  record['root']=parse(result.stdout,pid,expected);record['status']='observed'
 except Exception as error:
  record.update(status='observation_failed',error_type=type(error).__name__,error=str(error))
 finally:record['elapsed_seconds']=time.monotonic()-start
 return record

def classify(after,before):
 need(len(after)==3 and len(before)==2,'sample count')
 points=after+before
 roots=[x.get('root') for x in points]
 all_live=all(x.get('status')=='observed' and r is not None and r['state']=='L' for x,r in zip(points,roots))
 equal=all_live and all((r['pid'],r['identity'])==(roots[0]['pid'],roots[0]['identity']) for r in roots)
 return {'sampled_full_identity_equal':equal,'all_five_roots_observed_live':all_live,'sampled_points':5,'missing_or_failed_samples':sum(x.get('status')!='observed' or x.get('root') is None for x in points),'continuous_liveness_proven':False,'physical_reclamation_qualified':False}
