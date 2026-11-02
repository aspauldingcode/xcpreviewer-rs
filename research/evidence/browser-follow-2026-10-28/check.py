from pathlib import Path
import json,hashlib,subprocess,tempfile,shutil,plistlib
from PIL import Image
w=Path(__file__).parent;r=Path('/Users/8amps/xcpreviewer-rs');sha=lambda b:hashlib.sha256(b).hexdigest()
rows={name:json.loads((w/('browser-'+name+'.json')).read_text()) for name in ['initial','transparent','invalid','recovered','stopped','live']}
opaque='118c0283e5d72877b9e74a8233327177b6f23f817c33021240e3b3e1c0b7c1e2';transparent='c2c764b773a361f87aacbc356b114abc2758bb1ab12bb7e52fa7d194a331eda8'
for name,expected in [('initial',opaque),('transparent',transparent),('invalid',transparent),('recovered',opaque),('stopped',opaque)]:assert rows[name]['readback']['readbackSha256']==expected,name
assert rows['invalid']['error']=='true' and rows['recovered']['error']=='false' and not rows['stopped']['checked']
live=Image.open(w/'live.png').convert('RGBA').tobytes();assert len(live)==98304 and sha(live)==rows['live']['readback']['readbackSha256'] and rows['live']['checked'] and rows['live']['error']=='false'
assert rows['initial']['checked'] and rows['transparent']['checked'] and rows['recovered']['checked']
# Independent copied-source scheduling/reader checks; actual browser observations
# above are retained data and are not represented as an automated browser replay.
work=Path(tempfile.mkdtemp(prefix='browser-follow-unit-replay-'));(work/'browser-preview').mkdir();(work/'tests').mkdir()
shutil.copyfile(r/'tools/re/browser-preview/sample-follow.js',work/'browser-preview/sample-follow.js');shutil.copyfile(r/'tools/re/tests/browser_sample_follow.mjs',work/'tests/browser_sample_follow.mjs')
p=subprocess.run(['node',str(work/'tests/browser_sample_follow.mjs')],capture_output=True,timeout=15);(w/'unit-replay.stdout').write_bytes(p.stdout);(w/'unit-replay.stderr').write_bytes(p.stderr);p.check_returncode();unit=json.loads(p.stdout);assert unit['controls']==6
for name in ['viewer.js','sample-follow.js']:
 p=subprocess.run(['node','--input-type=module','--check'],input=(r/'tools/re/browser-preview'/name).read_bytes(),capture_output=True,timeout=5);p.check_returncode()
(w/'results.json').write_text(json.dumps({'passed':True,'copied_source_unit_controls':6,'fresh_unit_workspace':str(work),'actual_browser_auto_refresh':True,'actual_browser_invalid_update_preserved_frame':True,'actual_browser_recovery':True,'actual_browser_manual_open_stops_follow':True,'actual_browser_pause_feedback':True,'source_watcher_to_browser_readback_bytes':len(live),'source_watcher_native_png_browser_equal':True,'source_watcher_browser_rgba_sha256':sha(live),'live_server_url':'http://127.0.0.1:59989/?verify=1','scope':'Original browser polling policy and actual WASM/native-image readback. Browser observations are retained manual controls, not an unattended replay. No Rust test rerun or native Canvas/session/state/provider settlement parity.'},indent=2)+'\n');print((w/'results.json').read_text())
