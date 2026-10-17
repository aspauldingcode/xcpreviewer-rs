import sys,json,hashlib,subprocess
from pathlib import Path
p=Path(__file__).parent;sys.path.insert(0,str(p))
from admit import admitted
from record_admit import parsed,record,need
for n in ['compile','output-valid','fixture']:
 outer=parsed((p/(n+'-outer.json')).read_text());need(type(outer['node_exit']) is int and outer['node_exit']==0)
 row=parsed((p/(n+'-record.json')).read_text());record(row,n!='compile');need(row['source_sha256']==hashlib.sha256((p/'probe.c').read_bytes()).hexdigest() and row['binary_sha256']==hashlib.sha256((p/'probe').read_bytes()).hexdigest())
v=parsed((p/'sdk-identity.json').read_text());sdk=Path(v['sdk_root'])
for n,h in v['header_sha256'].items():need(hashlib.sha256((sdk/n).read_bytes()).hexdigest()==h)
e=parsed((p/'environment.json').read_text());need(e['this_wake_xcode_plist_sha256']==e['Xcode']['plist_sha256']);need(hashlib.sha256(Path('/System/Library/CoreServices/SystemVersion.plist').read_bytes()).hexdigest()==e['macOS']['plist_sha256'])
result=admitted(p);(p/'admission.json').write_text(json.dumps(result,indent=2)+'\n')
x=subprocess.run([sys.executable,'-O','-B',str(p/'admit.py')],capture_output=True,text=True,timeout=10);need(x.returncode==0);(p/'optimized-native-replay.json').write_text(json.dumps({'code':x.returncode,'stdout':x.stdout,'stderr':x.stderr},indent=2)+'\n')
print(json.dumps({'identities_verified':True,'admission':result}))
