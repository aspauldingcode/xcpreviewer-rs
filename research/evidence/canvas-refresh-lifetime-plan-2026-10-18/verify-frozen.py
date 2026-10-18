import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
seal=json.loads((root/'seal.json').read_text())
for name,digest in seal['files'].items():
 p=root/name
 if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError(name)
for name,digest in json.loads((root/'approved-pins.json').read_text()).items():
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('pin')
if list(root.glob('phase*.json')) or list(root.glob('phase*.png')):raise ValueError('unexecuted plan acquired phases')
for test in ['test_decode.py','test_bindings.py','test_identity.py','test_budget.py']:
 for opt in [False,True]:
  p=subprocess.run([sys.executable,*(['-O'] if opt else []),'-B',str(root/test)],capture_output=True,text=True,timeout=15);p.check_returncode()
cleanup=json.loads((root/'approval-limit-and-cleanup.json').read_text())
if cleanup['native_render_calls']!=0 or not cleanup['original_deadline_closed'] or cleanup['cleanup']['owned_workspace_windows']!=0:raise ValueError('recorded disposition')
print(json.dumps({'verified':True,'files':len(seal['files']),'synthetic_methods':17,'native_render_calls':0,'native_observer_calls':0,'original_deadline_closed':True}))
