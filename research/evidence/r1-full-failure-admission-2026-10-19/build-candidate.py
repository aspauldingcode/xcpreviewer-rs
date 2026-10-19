from pathlib import Path
import ast,json,hashlib
p=Path(__file__).resolve().parent;before=(p/'before.py').read_text();tree=ast.parse(before);conditions=[ast.dump(x.test,include_attributes=False) for x in ast.walk(tree) if isinstance(x,ast.Assert)]
class Change(ast.NodeTransformer):
 def visit_Assert(self,node):return ast.copy_location(ast.Expr(ast.Call(ast.Name('_require',ast.Load()),[self.visit(node.test)],[])),node)
 def visit_Call(self,node):
  node=self.generic_visit(node)
  if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='json' and node.func.attr=='loads':node.func=ast.Name('_json',ast.Load())
  return node
new=ast.unparse(ast.fix_missing_locations(Change().visit(tree)))+'\n'
new=new.replace("for (n, x) in m['files'].items():", "for (n, x) in m['files'].items():\n        _integer(x['bytes'])")
new=new.replace("compile = _json((e / 'compile.json').read_text())", "compile = _json((e / 'compile.json').read_text())\n    _integer(compile['code'])")
new=new.replace("wait = _json((e / 'wait.json').read_text())", "wait = _json((e / 'wait.json').read_text())\n    _integer(wait['code'])")
new=new.replace("parents.append(row['sender_pid'])", "_pid(row['sender_pid'])\n        _pid(row['receiver_pid'])\n        parents.append(row['sender_pid'])")
header='''"""Fail-closed frozen full-allocation failure/timeout evidence reader."""\nimport math\ndef _require(condition):\n    if not condition:raise AssertionError('Surface failure evidence rejected')\ndef _integer(value):\n    _require(type(value) is int and value>=0)\ndef _pid(value):\n    _require(type(value) is int and 1<value<=2147483647)\ndef _json(raw):\n    def pairs(items):\n        d={}\n        for k,v in items:\n            _require(k not in d)\n            d[k]=v\n        return d\n    def constant(v):raise AssertionError('Nonfinite JSON rejected')\n    v=json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)\n    def finite(x):\n        if type(x) is float:_require(math.isfinite(x))\n        elif type(x) is list:\n            for y in x:finite(y)\n        elif type(x) is dict:\n            for y in x.values():finite(y)\n    finite(v)\n    return v\n'''
new=header+new;after=ast.parse(new);after_conditions=[ast.dump(x.args[0],include_attributes=False) for x in ast.walk(after) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='_require' and x.args]
# Parser call renaming is the sole change inside original predicates.
def normalized(s):return s.replace("Attribute(value=Name(id='json', ctx=Load()), attr='loads', ctx=Load())","Name(id='_json', ctx=Load())")
if not all(normalized(c) in after_conditions for c in conditions):raise ValueError('Lost original predicate')
if any(isinstance(x,ast.Assert) for x in ast.walk(after)):raise ValueError('Remaining assertion')
(p/'after.py').write_text(new);(p/'preservation.json').write_text(json.dumps({'original_assertion_predicates':len(conditions),'all_preserved_as_require':True,'remaining_asserts':0,'before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':hashlib.sha256(new.encode()).hexdigest()},indent=2)+'\n')
print(len(conditions))
