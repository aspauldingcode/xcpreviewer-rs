"""Original file-boundary control, not a clean implementer or target probe."""
import errno,hashlib,json,os,platform,signal,sys
from pathlib import Path
signal.alarm(15)
root=Path('/input'); output=Path('/work'); rows=[]
expected=bytes(i%256 for i in range(1024))
raw=(root/'CONTROL.bin').read_bytes()
rows.append({'case':'allowed-input','pass':raw==expected,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
transformed=bytes(255-(i%256) for i in range(1024))
(output/'result.bin').write_bytes(raw[::-1]); actual=(output/'result.bin').read_bytes()
rows.append({'case':'allowed-output','pass':actual==transformed,'bytes':len(actual),'sha256':hashlib.sha256(actual).hexdigest()})
for label,path,op in [('input-write',root/'CONTROL.bin','write'),('root-write',Path('/outside-control.txt'),'write'),('unmounted-host-read',Path(os.environ['EXCLUDED_HOST_PATH']),'read'),('research-read',Path('/Users/8amps/xcpreviewer-rs/Cargo.toml'),'read'),('absolute-symlink-escape',root/'absolute-escape','read'),('relative-symlink-escape',root/'relative-escape','read')]:
    try:
        if op=='write': path.write_bytes(b'FORBIDDEN')
        else: path.read_bytes()
    except OSError as error:
        wanted=errno.EROFS if op=='write' else errno.ENOENT
        rows.append({'case':label,'pass':error.errno==wanted,'errno':error.errno,'expected_errno':wanted})
    else: rows.append({'case':label,'pass':False,'unexpected_success':True})
status=Path('/proc/self/status').read_text(); fields={s.split(':',1)[0]:s.split(':',1)[1].strip() for s in status.splitlines() if ':' in s}
interfaces=[line.split(':',1)[0].strip() for line in Path('/proc/net/dev').read_text().splitlines() if ':' in line]
r={'schema':1,'rows':rows,'passed':all(row['pass'] is True for row in rows),'uid':os.getuid(),'gid':os.getgid(),'host':platform.uname()._asdict(),'python':sys.version,'cap_eff':fields.get('CapEff'),'no_new_privs':fields.get('NoNewPrivs'),'interfaces':interfaces,'model_tool_isolation_proven':False,'handoff_approved':False}
(output/'result.json').write_text(json.dumps(r,indent=2)); print(json.dumps({'passed':r['passed'],'cases':len(rows)}))
sys.exit(0 if r['passed'] else 1)
