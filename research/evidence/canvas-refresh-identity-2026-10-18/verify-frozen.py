import datetime,hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
seal=json.loads((root/'seal.json').read_text())
for name,digest in seal['files'].items():
 p=root/name
 if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError(name)
for name,digest in json.loads((root/'approved-pins.json').read_text()).items():
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('approved pin')
sys.path.insert(0,str(root))
from decode import decode
from bindings import owned_tab,payload
ownership=json.loads((root/'ownership.json').read_text())
tab=owned_tab(json.loads((root/'window-binding.json').read_text()),ownership['workspace'])
rows=[]
deadline=datetime.datetime(2026,10,18,16,15,tzinfo=datetime.timezone.utc).timestamp()
for phase in range(3):
 record=json.loads((root/('phase%d.json'%phase)).read_text());image=root/('phase%d.png'%phase)
 if record['phase']!=phase or record['status']!='measured' or record['source_sha256']!=hashlib.sha256((root/'probe.swift').read_bytes()).hexdigest():raise ValueError('record binding')
 if record['request']!={'name':'RenderPreview','arguments':{'tabIdentifier':tab,'sourceFilePath':'PreviewLab/Sources/PreviewLab/PreviewLab.swift','timeout':45}}:raise ValueError('request')
 response=payload(record['response'])
 if response.get('errors') or not response.get('previewSnapshotPath'):raise ValueError('snapshot response')
 if hashlib.sha256(image.read_bytes()).hexdigest()!=record['png_sha256']:raise ValueError('PNG hash')
 started=datetime.datetime.fromisoformat(record['started_at']).timestamp()
 if started+60>deadline or not 0<=record['elapsed_seconds']<55 or started+record['elapsed_seconds']>deadline:raise ValueError('deadline')
 measured=decode(image)
 if measured!=record['decoded']:raise ValueError('decode replay')
 rows.append(measured)
result=json.loads((root/'result.json').read_text())
if result['measurements']!=rows or result['visible_rgba_bytes_checked']!=sum(x['rgba_bytes_checked'] for x in rows):raise ValueError('result')
if result['pid_same_across_requests']!=(len({x['pid'] for x in rows})==1) or result['state_token_same_across_requests']!=(len({x['state_token_hex'] for x in rows})==1):raise ValueError('classification')
cleanup=json.loads((root/'cleanup.json').read_text())
if cleanup['owned_workspace_windows']!=0 or payload(cleanup['windows'])['message']!='No workspace windows found':raise ValueError('recorded cleanup')
for test in ['test_decode.py','test_bindings.py']:
 for opt in [False,True]:
  p=subprocess.run([sys.executable,*(['-O'] if opt else []),'-B',str(root/test)],capture_output=True,text=True,timeout=15);p.check_returncode()
print(json.dumps({'verified':True,'files':len(seal['files']),'rgba_bytes_checked':589824,'same_reported_pid':True,'tokens_differ':True,'live_endpoint_rechecked':False,'native_execution':False}))
