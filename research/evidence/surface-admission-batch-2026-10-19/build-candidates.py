from pathlib import Path
import ast,json,hashlib
p=Path(__file__).resolve().parent;rows=[]
class Change(ast.NodeTransformer):
 def visit_Assert(self,n):return ast.copy_location(ast.Expr(ast.Call(ast.Name('_require',ast.Load()),[self.visit(n.test)],[])),n)
for f in sorted((p/'before').glob('*.py')):
 t=ast.parse(f.read_text());pred=[ast.dump(n.test,include_attributes=False) for n in ast.walk(t) if isinstance(n,ast.Assert)]
 out="def _require(condition):\n    if not condition:\n        raise AssertionError('Surface lifecycle evidence rejected')\n\n"+ast.unparse(ast.fix_missing_locations(Change().visit(t)))+'\n';q=p/'after'/f.name;q.write_text(out);a=ast.parse(out);calls=[ast.dump(n.args[0],include_attributes=False) for n in ast.walk(a) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_require' and n.args]
 if pred!=calls or any(isinstance(n,ast.Assert) for n in ast.walk(a)):raise ValueError(f.name+' predicate preservation')
 rows.append({'reader':f.name,'predicates':len(pred),'all_preserved_in_order':True,'before_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
(p/'preservation.json').write_text(json.dumps(rows,indent=2)+'\n');print(sum(x['predicates'] for x in rows))
