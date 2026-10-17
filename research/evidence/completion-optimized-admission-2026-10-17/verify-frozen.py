"""Offline only: integrity, predicate preservation, frozen fault matrix."""
import ast,hashlib,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent
seal=json.loads((p/'seal.json').read_text())
for name,digest in seal['files'].items():
 f=p/name
 if f.is_symlink() or hashlib.sha256(f.read_bytes()).hexdigest()!=digest:raise ValueError('Seal mismatch: '+name)
for name in ['verify_completion_guard.py','verify_post_completion_delay.py']:
 original=ast.parse((p/('original-'+name)).read_text());fixed=ast.parse((p/name).read_text())
 a=[ast.dump(n.test) for n in ast.walk(original) if isinstance(n,ast.Assert)]
 b=[ast.dump(n.args[0]) for n in ast.walk(fixed) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_require']
 if a!=b or any(isinstance(n,ast.Assert) for n in ast.walk(fixed)):raise ValueError('Predicate drift')
for relative,pin in json.loads((p/'anchors.json').read_text()).items():
 anchor=Path('/Users/8amps/xcpreviewer-rs')/relative
 if hashlib.sha256(anchor.read_bytes()).hexdigest()!=pin:raise ValueError('Historical anchor drift')
matrix=json.loads((p/'matrix.json').read_text())
if len(matrix)!=48 or sum(x['accepted'] and x['fault']!='positive' and x['version']=='original' for x in matrix)!=10:raise ValueError('Matrix invalid')
print(json.dumps({'sealed_files':len(seal['files']),'predicates_preserved':50,'configurations':48,'native_execution':False}))
