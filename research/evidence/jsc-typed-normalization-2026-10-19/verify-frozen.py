"""Read-only sealed replay; no engine/native execution."""
from pathlib import Path
import hashlib,json,importlib.util
from phase_prerequisites import parsed,require as need
p=Path(__file__).resolve().parent
seal=parsed((p/'seal.json').read_text())
files={str(q.relative_to(p)) for q in p.rglob('*') if q.is_file() and q.name!='seal.json' and '__pycache__' not in q.parts}
need(files==set(seal['files']),'inventory')
for n,h in seal['files'].items():need(not (p/n).is_symlink() and hashlib.sha256((p/n).read_bytes()).hexdigest()==h,'seal')
sp=importlib.util.spec_from_file_location('recorded',p/'verify-recorded.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
result=v.verify(p)
need(result==parsed((p/'result.json').read_text()),'result')
print(json.dumps(result))
