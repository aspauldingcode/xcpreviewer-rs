"""Additional frozen timeline validation; no native execution or edited acquisition pins."""
from pathlib import Path
import json,datetime,importlib.util
from phase_prerequisites import parsed,require as need
from admit import admit
ROOT=Path(__file__).resolve().parent
def verify(root):
 p=Path(root);result=admit(p);times=[];deadline=datetime.datetime(2026,10,19,9,55,tzinfo=datetime.timezone.utc)
 for phase in ['compile','output-valid','fixture']:
  v=parsed((p/(phase+'-started.json')).read_text());t=datetime.datetime.fromisoformat(v['started_at']);need(v['phase']==phase and v['deadline_utc']=='2026-10-19T09:55:00Z' and t.tzinfo is not None and t<deadline,'start timeline');times.append(t)
 completed=datetime.datetime.fromisoformat(parsed((p/'completed.json').read_text())['completed_at']);need(times==sorted(times) and times[-1]<completed<deadline,'phase order')
 out=parsed(parsed((p/'fixture-record.json').read_text())['record']['stdout']);result['environment']=out['environment'];result['scalar_dispatches']=out['scalar_dispatches'];result['host_invalid_inputs_rejected']=len(out['invalid_inputs'])
 return result
if __name__=='__main__':print(json.dumps(verify(ROOT)))
