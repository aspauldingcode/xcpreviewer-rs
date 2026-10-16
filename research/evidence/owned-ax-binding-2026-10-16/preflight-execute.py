import sys,hashlib,subprocess,json
from pathlib import Path
r=Path('/Users/8amps/xcpreviewer-rs');root=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
with Controller().lock():
 phase=sys.argv[1]
 if phase not in ['compile','run']:raise ValueError('Unknown phase')
 expected=json.loads((root/'approved-pins.json').read_text())
 for name,digest in expected.items():
  if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Approved source changed')
 if phase=='run':
  c=json.loads((root/'compile-record.json').read_text())
  if c['error'] or c['record']['report']['target_code']!=0 or c['record']['report']['drained'] is not True:raise ValueError('Compile not admitted')
  if hashlib.sha256((root/'probe').read_bytes()).hexdigest()!=c['binary_sha256']:raise ValueError('Binary changed')
 p=subprocess.run(['/etc/profiles/per-user/8amps/bin/node',str(root/'run_guard.js'),phase],capture_output=True,text=True,timeout=40 if phase=='compile' else 20)
 print(p.stdout+p.stderr)
 (root/(phase+'-outer.json')).write_text(json.dumps({'node_exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n')
 sys.exit(p.returncode)
