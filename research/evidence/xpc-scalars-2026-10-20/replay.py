"""Run owned native cross-process controls serially under the controller lock."""
from pathlib import Path
import subprocess,sys
r=Path('/Users/8amps/xcpreviewer-rs');sys.path.insert(0,str(r/'tools/re'));from reloop.core import Controller
with Controller().lock():
 subprocess.run([sys.executable,str(Path(__file__).with_name('run.py')),sys.argv[1]],check=True,timeout=240)
