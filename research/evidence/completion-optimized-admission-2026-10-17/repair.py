import ast
from pathlib import Path
HERE=Path(__file__).resolve().parent
for name in ['verify_completion_guard.py','verify_post_completion_delay.py']:
 s=(HERE/('original-'+name)).read_text();t=ast.parse(s);lines=s.splitlines(keepends=True);offset=[0]
 for line in lines:offset.append(offset[-1]+len(line))
 changes=[]
 for n in ast.walk(t):
  if isinstance(n,ast.Assert):
   start=offset[n.lineno-1]+n.col_offset;end=offset[n.end_lineno-1]+n.end_col_offset
   changes.append((start,end,'_require('+ast.get_source_segment(s,n.test)+')'))
 for start,end,replacement in sorted(changes,reverse=True):s=s[:start]+replacement+s[end:]
 s=s.replace('\n\ndef verify(folder):','\n\ndef _require(condition):\n    if not condition:\n        raise AssertionError("Completion evidence rejected")\n\n\ndef verify(folder):',1)
 (HERE/name).write_text(s)
 before=[ast.dump(n.test) for n in ast.walk(t) if isinstance(n,ast.Assert)]
 after=[ast.dump(n.args[0]) for n in ast.walk(ast.parse(s)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_require']
 if before!=after:raise ValueError('Predicate drift')
 print(name,len(before))
