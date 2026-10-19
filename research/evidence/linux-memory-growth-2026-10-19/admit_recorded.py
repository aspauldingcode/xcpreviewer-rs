"""Post-acquisition strict receipt correction; original approved source pins retained."""
from pathlib import Path
import json
from phase_prerequisites import parsed,require as need,integer
import admit

def observed(root):
 p=Path(root);plan=parsed((p/'plan.json').read_text());c=parsed((p/'container-cleanup.json').read_text())
 need(integer(c['inspect_exit']) and 0<=c['inspect_exit']<=255,'typed inspect exit')
 if c['inspect_exit']==0:need(c['inspect_owner']==plan['owner'],'inspected ownership')
 else:need(c['inspect_owner'] is None,'absent inspect ownership')
 return admit.observed(p)
if __name__=='__main__':print(json.dumps(observed(Path(__file__).resolve().parent),sort_keys=True))
