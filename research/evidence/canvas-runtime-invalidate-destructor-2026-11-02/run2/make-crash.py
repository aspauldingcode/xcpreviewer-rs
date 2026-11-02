from pathlib import Path
import json,time
r=Path(__file__).parent;pid=json.loads((r/'native-cancel-reentry.result.json').read_text())['pid']
found=False
for attempt in range(30):
 for p in sorted(Path.home().joinpath('Library/Logs/DiagnosticReports').glob('native-*.ips'),key=lambda p:p.stat().st_mtime,reverse=True)[:15]:
  s=p.read_text()
  try:d=json.loads(s[s.index('\n')+1:])
  except ValueError:continue
  if d.get('pid')!=pid:continue
  row={k:d.get(k) for k in ['pid','exception','termination','asi']};row['frames']=[]
  for th in d['threads']:
   if th.get('triggered'):
    for f in th['frames'][:16]:
     im=d['usedImages'][f['imageIndex']];row['frames'].append({'image':im.get('name'),'offset':hex(f['imageOffset']),'symbol':f.get('symbol')})
  (r/'cancel-reentry-crash.json').write_text(json.dumps(row,indent=2)+'\n');print('Captured matching owned crash',pid);found=True;break
 if found:break
 time.sleep(.1)
if not found:raise RuntimeError('Matching owned crash report not available; negative failure unclassified')
