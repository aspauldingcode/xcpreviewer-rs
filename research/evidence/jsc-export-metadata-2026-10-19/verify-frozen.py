"""Read-only frozen metadata/failure verification; never launches an engine."""
from pathlib import Path
import sys,json,hashlib,re,datetime
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'metadata-only'))
from phase_prerequisites import parsed,require as need,receipt,integer
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def observations(root):
 root=Path(root);results=[]
 for label in ['first-rejection','changed-rejection','metadata-only']:
  p=root/label
  for n,h in parsed((p/'approved-pins.json').read_text()).items():need(H(p/n)==h,'source pin')
  need(H(p/'probe.wasm')=='460ce52e8cfb8034e424a87c1e0647441769833137c4d39f4ad8ffc103b90d43','owned module')
  source=H(p/'probe.c');binary='b9c4f88f75f852a573f45bec82c9f7bd637b059c1f70efaf9a12a51cee0bbb48'
  for phase in ['compile','output-valid']:
   receipt(p,phase,source,binary)
  rea=parsed((p/'rea-identity.json').read_text());need(rea['owned_binary_sha256']==binary and rea['open_result']['sha256']==binary and rea['architecture']=='arm64' and rea['closed'] is True and rea['server_identity']['package']['version']=='6.2.0','REA identity')
  deadline=datetime.datetime(2026,10,19,9,45,tzinfo=datetime.timezone.utc)
  for phase in ['compile','output-valid','fixture']:
   s=parsed((p/(phase+'-started.json')).read_text());need(s['phase']==phase and s['deadline_utc']=='2026-10-19T09:45:00Z' and datetime.datetime.fromisoformat(s['started_at'])<deadline,'start budget')
  c=parsed((p/'completed.json').read_text());need(c['deadline_utc']=='2026-10-19T09:45:00Z' and datetime.datetime.fromisoformat(c['completed_at'])<deadline,'completion budget')
  row=parsed((p/'fixture-record.json').read_text());r=row['record'];outer=parsed((p/'fixture-outer.json').read_text());report=r['report'];need(row['source_sha256']==source and row['binary_sha256']==binary,'fixture binding')
  need(report['kind']=='complete' and report['failure'] is None and report['drained'] is True and integer(report['remaining_observed'],0) and r['emergencyClosed'] is False and r['privateAbortRequested'] is False,'lifecycle')
  for stream in ['stdout','stderr']:
   b=r[stream].encode();need(integer(r[stream+'Bytes'],len(b)) and r[stream+'Sha256']==hashlib.sha256(b).hexdigest(),'stream integrity')
  need(not (p/'owned-documents').exists() or list((p/'owned-documents').iterdir())==[],'zero buffers')
  if label!='metadata-only':
   need(integer(outer['node_exit'],1) and integer(report['target_code'],2) and row['error']=='Error: Observed compiler failed: 2' and r['stdout']=='','retained failure')
   message='module shape' if label=='first-rejection' else 'semantic module shape'
   need(re.fullmatch(r'owned_tree_pid:[1-9][0-9]*\nowned_js_exception:Error: '+message+r'\nrejected:evaluation\n',r['stderr']) is not None,'failure diagnosis')
   rejected=False
   try:receipt(p,'fixture',source,binary)
   except ValueError:rejected=True
   need(rejected,'failed receipt cannot qualify')
   results.append({'attempt':label,'target_exit':2,'qualified':False});continue
  receipt(p,'fixture',source,binary);out=parsed(r['stdout'])
  need(out['status']=='metadata_only' and out['webassembly_type']=='object' and out['module_valid'] is True and integer(out['module_bytes'],81) and out['imports']==[],'metadata observation')
  need(integer(out['pid']) and 1<out['pid']<2**31 and r['stderr']=='owned_tree_pid:'+str(out['pid'])+'\n','pid')
  need(out['engine']=='public JavaScriptCore JSContext' and out['environment']=={'framework_identifier':'com.apple.JavaScriptCore','framework_path':'/System/Library/Frameworks/JavaScriptCore.framework','framework_version':'21624.2.5.11.4','machine':'arm64','os_version':'Version 26.5.1 (Build 25F80)','release':'25.5.0','system':'Darwin'},'measured environment')
  expected=[{'name':n,'kind':'function','type':{'parameters':['i32'],'results':['i32']}} for n in ['multiplyBits','divideBits']]
  need(out['exports']==expected and out['export_key_order']==[['name','kind','type']]*2 and out['export_own_property_names']==[['name','kind','type']]*2,'typed descriptor')
  need(out['rows']==[] and integer(out['scalar_dispatches'],0) and all(out[k] is False for k in ['native_UI_execution','product_integration','non_Apple_OS_verified','canvas_qualified']),'scope')
  results.append({'attempt':label,'metadata_verified':True,'extra_descriptor_field':'type','scalar_conformance':False,'full_bytes_compared':0,'environment':out['environment']})
 return {'attempts':results,'both_failures_retained':True,'property_order_only_explanation_supported':False,'second_engine_scalar_conformance':False,'canvas_qualified':False}
def verify(root):
 root=Path(root);seal=parsed((root/'seal.json').read_text());actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='seal.json' and '__pycache__' not in p.parts}
 need(actual==set(seal['files']),'inventory')
 for n,h in seal['files'].items():need(not (root/n).is_symlink() and H(root/n)==h,'seal')
 return observations(root)
if __name__=='__main__':print(json.dumps(verify(ROOT)))
