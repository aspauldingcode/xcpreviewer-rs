from pathlib import Path
import subprocess,sys,json
w=Path(__file__).parent;sys.path.insert(0,str(w));from validator import validate
raw=Path('/Users/8amps/xcpreviewer-rs/research/raw/hardware-event-20261020');clang='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang'
p=subprocess.run([clang,'-Wall','-Wextra','-Werror',str(w/'worker.m'),'-framework','Foundation','-framework','CoreGraphics','-o',str(w/'worker')],capture_output=True,timeout=30);(raw/'worker-build.log').write_bytes(p.stdout+p.stderr);p.check_returncode()
rows=[]
for n,t in enumerate([1,10,22]):
 p=raw/'isolated'/f'event-{n}.bin';x=validate(w/'worker',p);assert x=={'accepted':True,'type':t,'timestamp':123456789,'flags':131072,'status':'accepted'};rows.append(x)
for name,b,expect in [('empty',b'','rejected'),('text',b'not an event','rejected'),('truncated',(raw/'isolated/event-0.bin').read_bytes()[:130],'crash')]:
 p=raw/(name+'.bin');p.write_bytes(b);x=validate(w/'worker',p);assert x['accepted'] is False and x['status']==expect;rows.append(x)
# Faults in the worker boundary itself cannot turn into acceptance.
for name,body,status in [('false-receipt','print("{}")','invalid_response'),('late-receipt','import time;time.sleep(5)','timeout'),('failed-receipt','import sys;print(\'{"accepted":true,"type":1,"timestamp":1,"flags":0}\');sys.exit(1)','worker_error')]:
 p=w/name;p.write_text('#!/usr/bin/python3\n'+body+'\n');p.chmod(0o700);x=validate(p,raw/'empty.bin',timeout=.2);assert x['accepted'] is False and x['status']==status;rows.append(x)
(w/'worker-check.json').write_text(json.dumps({'cases':rows,'valid':3,'native_reject':2,'native_crash_contained':1,'boundary_faults_rejected':3},indent=2)+'\n');print('3 native accept,2 reject,1 crash contained;3 worker faults rejected')
