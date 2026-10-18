import datetime,hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
seal=json.loads((root/'seal.json').read_text())
for name,digest in seal['files'].items():
 p=root/name
 if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError(name)
for name,digest in json.loads((root/'approved-pins.json').read_text()).items():
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('pin')
sys.path.insert(0,str(root))
from identity import parse,classify,HELPER_SHA,valid_identity
from decode import decode
from bindings import payload,owned_tab
ownership=json.loads((root/'ownership.json').read_text())
tab=owned_tab(json.loads((root/'window-binding.json').read_text()),ownership['workspace'])
source=hashlib.sha256((root/'probe.swift').read_bytes()).hexdigest()
after=[];before=[];measurements=[]
def check_snapshot(value,pid,expected):
 if value['pid']!=pid or value['expected_identity']!=expected or value['status']!='observed' or type(value['returncode']) is not int or value['returncode']!=0 or value['helper_sha256']!=HELPER_SHA:raise ValueError('snapshot binding')
 selector=str(pid) if expected is None else '%d:%d:%d'%(pid,*expected[:2])
 if value['selector']!=selector or len(value['stderr'].encode())>4096 or not 0<=value['elapsed_seconds']<3:raise ValueError('snapshot guard')
 observed=parse(value['stdout'],pid,expected)
 if observed!=value['root'] or observed is None or observed['state']!='L':raise ValueError('snapshot replay')
 return value
for phase in range(3):
 record=json.loads((root/('phase%d.json'%phase)).read_text())
 if record['phase']!=phase or record['status']!='measured' or record['source_sha256']!=source:raise ValueError('phase')
 if record['request']!={'name':'RenderPreview','arguments':{'tabIdentifier':tab,'sourceFilePath':'PreviewLab/Sources/PreviewLab/PreviewLab.swift','timeout':45}}:raise ValueError('request')
 response=payload(record['response'])
 if response.get('errors') or not response.get('previewSnapshotPath'):raise ValueError('response')
 image=root/('phase%d.png'%phase)
 if hashlib.sha256(image.read_bytes()).hexdigest()!=record['png_sha256']:raise ValueError('image hash')
 measured=decode(image)
 if measured!=record['decoded']:raise ValueError('pixels')
 measurements.append(measured)
 if phase:
  previous=after[-1]['root'];before.append(check_snapshot(record['before_identity'],previous['pid'],previous['identity']))
 after.append(check_snapshot(record['after_identity'],measured['pid'],None))
 deadline=datetime.datetime(2026,10,18,17,12,tzinfo=datetime.timezone.utc).timestamp();started=datetime.datetime.fromisoformat(record['started_at']).timestamp()
 if started+70>deadline or not 0<=record['elapsed_seconds']<70 or started+record['elapsed_seconds']>deadline:raise ValueError('deadline')
result=json.loads((root/'result.json').read_text())
if result['measurements']!=measurements or result['identity_observations']!=classify(after,before) or result['visible_rgba_bytes_checked']!=589824:raise ValueError('classification')
if result['state_token_same_across_requests']!=(len({m['state_token_hex'] for m in measurements})==1):raise ValueError('token summary')
cleanup=json.loads((root/'cleanup.json').read_text())
if cleanup['owned_workspace_windows']!=0 or payload(cleanup['windows'])['message']!='No workspace windows found' or cleanup['final_source_sha256']!=source:raise ValueError('cleanup/source')
for test in ['test_decode.py','test_bindings.py','test_identity.py','test_budget.py']:
 for opt in [False,True]:
  p=subprocess.run([sys.executable,*(['-O'] if opt else []),'-B',str(root/test)],capture_output=True,text=True,timeout=15);p.check_returncode()
print(json.dumps({'verified':True,'files':len(seal['files']),'rgba_bytes':589824,'identity_samples':5,'sampled_identity_equal':result['identity_observations']['sampled_full_identity_equal'],'native_execution':False,'continuous_liveness_proven':False}))
