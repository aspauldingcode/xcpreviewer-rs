import sys,pathlib,json,hashlib
r=pathlib.Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'))
from reloop.core import Controller
from reloop.graphloop import adopt_verified,inspect
c=Controller();report=adopt_verified(c,'primary-live-wasm-swap','20261011T093849Z-primary-live-wasm-swap-6bc05646','a7be4b7c9d6e0aa1a0af7d151636335fe68418787e821d073323d304303f4c15')
with c.lock():
 e=r/'research/evidence/graph-adoption-2026-10-11';e.mkdir();(e/'adoption.json').write_text(json.dumps(report,indent=2)+'\n');view=inspect(c);view.pop('communication',None);(e/'frontier.json').write_text(json.dumps(view,indent=2)+'\n')
 for name in ['experiment.json','manifest.json']: (e/('reference-'+name)).write_bytes((c.runs/report['run_id']/name).read_bytes())
 (e/'graphloop.py').write_bytes((r/'tools/re/reloop/graphloop.py').read_bytes());print(json.dumps({'verification':report['verification'],'candidates':view['candidates'],'milestones':view['all_milestones_complete']},indent=2))
