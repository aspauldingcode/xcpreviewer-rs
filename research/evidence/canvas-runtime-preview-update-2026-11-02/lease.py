from pathlib import Path
import fcntl,subprocess,time,json,hashlib
p=Path(__file__).parent
with open('/Users/8amps/xcpreviewer-rs/research/state/controller.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for name,digest in [('PreviewsScenes','e785b5947cd0ae70ff8977485f73f7181b6ed07c958ef29ce263ffa06397bc09'),('PreviewsUI','26037ce436a19205977e4c5b879c8b46a1ac87f19fef25ffb5e14282ba189fab')]:
  image=Path('/Applications/Xcode.app/Contents/SharedFrameworks')/(name+'.framework/Versions/A')/name
  assert hashlib.sha256(image.read_bytes()).hexdigest()==digest
 assert subprocess.run(['pgrep','-x','Xcode'],capture_output=True).returncode==1,'Xcode running; do not launch into unknown identity'
 result=subprocess.run(['open','-g','-a','/Applications/Xcode.app','/Users/8amps/xcpreviewer-rs/research/build/preview-workspaces/preview-ca9cbc8786144517b3a14ef57a90e08b/PreviewLab.xcodeproj'],capture_output=True,timeout=8)
 (p/'launch.json').write_text(json.dumps({'code':result.returncode,'stderr':result.stderr.decode(),'background':True,'user_process_termination':False},indent=2)+'\n');assert result.returncode==0
 (p/'ready').touch();end=time.monotonic()+180
 while time.monotonic()<end and not (p/'stop').exists():time.sleep(.1)
 (p/'controller-released').touch()
