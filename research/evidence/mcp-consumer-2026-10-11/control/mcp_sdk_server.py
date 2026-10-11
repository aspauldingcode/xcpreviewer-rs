"""Owned stdio supervisor: preserve streams, retain actual child wait status."""
import json,subprocess,sys
from pathlib import Path
runtime,config,source,root,waitfile=sys.argv[1:]
p=subprocess.Popen(['/etc/profiles/per-user/8amps/bin/node',str(Path(runtime)/'tools/re/preview_mcp_stdio.js'),config,source,root,'10000'])
try:
 code=p.wait(timeout=12)
except subprocess.TimeoutExpired:
 p.terminate()
 try:p.wait(timeout=2)
 except subprocess.TimeoutExpired:p.kill();p.wait(timeout=2)
 Path(waitfile).write_text(json.dumps({'timeout':True,'code':p.returncode}))
 raise
Path(waitfile).write_text(json.dumps({'timeout':False,'code':code}))
raise SystemExit(code)
