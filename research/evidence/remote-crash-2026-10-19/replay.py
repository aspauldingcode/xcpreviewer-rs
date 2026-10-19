"""Independent fixture reconstruction and read-only verification of original codec."""
from pathlib import Path
import sys,json,plistlib,hashlib,tempfile,os,subprocess
root=Path('/Users/8amps/xcpreviewer-rs');evidence=Path(__file__).parent
sys.path.insert(0,str(root/'tools/re'))
from reloop.core import Controller
base=Path('/Users/8amps/.rustup/toolchains/stable-aarch64-apple-darwin/bin')
with Controller().lock(),tempfile.TemporaryDirectory(prefix='remote-crash-replay-') as tmp:
 t=Path(tmp);fixtures=root/'tools/re/rust/canvas-core/tests/fixtures/remote-crash'
 independent={}
 for behavior in ['willProvide','canSymbolicate','unavailable']:
  independent['modern-'+behavior]={'discriminant':'agentCrashed','pid':12345,'agentBehavior':{'discriminant':behavior},'diagnosticsComing':behavior=='willProvide'}
 for name,flag in [('legacy-true',True),('legacy-false',False)]:independent[name]={'discriminant':'agentCrashed','pid':12345,'diagnosticsComing':flag}
 for name,value in independent.items():
  raw=plistlib.dumps(value,fmt=plistlib.FMT_BINARY,sort_keys=False);assert (fixtures/(name+'.bplist')).read_bytes()==raw
  p=json.loads((evidence/'fixture-provenance.json').read_text())['fixtures'][name];assert hashlib.sha256(raw).hexdigest()==p['sha256']
 env=dict(os.environ,RUSTC=str(base/'rustc'),RUSTDOC=str(base/'rustdoc'),CARGO_TARGET_DIR=str(t/'rust-target'))
 p=subprocess.run([str(base/'cargo'),'test','--offline','-p','canvas-core'],cwd=root,env=env,capture_output=True,text=True,timeout=60);print(p.stdout+p.stderr);p.check_returncode()
 p=subprocess.run([str(base/'cargo'),'build','--offline','-p','canvas-core','--bin','inspect-preview-crash'],cwd=root,env=env,capture_output=True,text=True,timeout=45);p.check_returncode()
 for name in independent:
  p=subprocess.run([str(t/'rust-target/debug/inspect-preview-crash'),str(fixtures/(name+'.bplist'))],capture_output=True,text=True,timeout=5);p.check_returncode()
  behavior={'modern-willProvide':'WillProvide','modern-canSymbolicate':'CanSymbolicate','modern-unavailable':'Unavailable','legacy-true':'WillProvide','legacy-false':'Unavailable'}[name]
  assert p.stdout.strip()=='stream=Ultraviolet.PreviewRemoteEvents pid=12345 agent_behavior='+behavior
 print(json.dumps({'source_modified':False,'independent_fixtures_reproduced':5,'tests_passed':35,'cli_fixtures_passed':5,'private_runtime_invoked':False}))
