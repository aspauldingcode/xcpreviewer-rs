"""Request an experiment phase and wait at most six seconds for collector acknowledgement."""
from pathlib import Path
import argparse,json,time
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('label',choices=['idle-start','idle-end','refresh-start','refresh-return','refresh-settled','edit','edit-settled','restore','restore-settled']);a=p.parse_args();r=a.directory
assert (r/'ready').exists(),'Collector not ready'
assert not (r/(a.label+'.ack')).exists(),'Duplicate phase'
assert not any(json.loads(x)['stage']=='session-ended-no-target-termination' for x in (r/'events.jsonl').read_text().splitlines()),'Collector ended'
(r/('command-'+a.label)).touch();end=time.monotonic()+6
while time.monotonic()<end:
 if (r/(a.label+'.ack')).exists():print(a.label);break
 time.sleep(.05)
else:raise TimeoutError('Phase acknowledgement missing')
