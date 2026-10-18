import sys,json
from pathlib import Path
from decoder import expected,canonical,filename,record
p=Path(__file__).resolve().parent;stage=int(sys.argv[1]);view=sys.argv[2]
if stage not in (1,2,3):raise ValueError('Stage')
plan=json.loads((p/'experiment.json').read_text());obs=json.loads((p/('receipt-observation-%d.json'%stage)).read_text());rows=obs['records']
if len(rows)!=stage:raise ValueError('Expected exact transcript count')
live=rows[0]['live_identity']
if not live or live['state']!='L' or type(live['pid']) is not int or not live['identity'][2].endswith('/Build/Products/Debug/PreviewLab.app/Contents/MacOS/PreviewLab'):raise ValueError('Live owned app identity')
identity={'nonce':plan['nonce'],'pid':live['pid'],'view':view}
if stage>1:
 baseline=json.loads((p/'validated-1.json').read_text())
 if identity!=baseline['identity'] or live!=baseline['live_identity']:raise ValueError('Session identity changed')
raw={x['name']:bytes.fromhex(x['raw_hex']) for x in rows}
if len(raw)!=stage or any(x['live_identity']!=live for x in rows):raise ValueError('Identity/namespace')
wants=[expected(identity,'appear' if i==0 else 'increment',i,i) for i in range(stage)]
if set(raw)!={filename(x) for x in wants}:raise ValueError('Expected namespace')
for x in wants:record(raw[filename(x)],filename(x),identity,x['event'],x['sequence'],x['count'])
result={'stage':stage,'identity':identity,'live_identity':live,'bytes_compared':sum(map(len,raw.values())),'raw_hex':{k:v.hex() for k,v in raw.items()},'scope':'Finite sampled identity and complete owned event transcript, not continuous lifetime/private Canvas transport.'}
(p/('validated-%d.json'%stage)).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'stage':stage,'count':stage-1,'pid':live['pid'],'bytes':result['bytes_compared']}))
