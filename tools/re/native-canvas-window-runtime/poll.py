"""Request one existing collector snapshot; wait for its native-main acknowledgement."""
from pathlib import Path
import argparse,json,time
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('label',choices=['baseline','unpinned','new-tab','after-close','restored']);a=p.parse_args();r=a.directory
rows=[json.loads(v) for v in (r/'events.jsonl').read_text().splitlines()];assert not any(v['stage']=='session-ended-no-target-termination' for v in rows),'Collector already ended'
out=r/(a.label+'.json');assert not out.exists(),'Duplicate snapshot label';(r/('poll-'+a.label)).touch();end=time.monotonic()+6
while time.monotonic()<end:
 if out.exists():
  try:value=json.loads(out.read_text())
  except json.JSONDecodeError:time.sleep(.02);continue
  print(json.dumps(value));break
 if any(json.loads(v)['stage']=='session-ended-no-target-termination' for v in (r/'events.jsonl').read_text().splitlines()):raise RuntimeError('Collector ended before acknowledgement')
 time.sleep(.05)
else:raise TimeoutError('Native snapshot acknowledgement not observed')
