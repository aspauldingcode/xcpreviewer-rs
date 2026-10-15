"""Mechanical source/asset inventory. Never infers originality or clean-room eligibility."""
import argparse
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path
from canvas_graph import ROOT, safe

ROOTS=['Cargo.toml','Cargo.lock','README.md','examples','tools/re/rust/canvas-core','tools/re/reloop','tools/re/preview_stdio.js','tools/re/preview_mcp_stdio.js','tools/re/preview_cli.py','tools/re/rust_source_cli.py']
ASSETS={'.png','.jpg','.jpeg','.svg','.ttf','.otf','.wav','.mp3','.ico','.icns'}
MAX_FILE=1048576


def snapshot(path):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):raise ValueError('Nonregular inventory file')
        if before.st_size>MAX_FILE:raise ValueError('Inventory file size limit')
        with os.fdopen(os.dup(fd),'rb') as stream:raw=stream.read(MAX_FILE+1)
        after=os.fstat(fd)
        identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        if len(raw)>MAX_FILE or identity(before)!=identity(after) or len(raw)!=after.st_size:raise ValueError('File changed during inventory')
        return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    finally:os.close(fd)


def inventory(root,roots=None):
    root=Path(root).resolve();roots=ROOTS if roots is None else roots
    for name in roots:safe(root,name)
    def git(*args):
        r=subprocess.run(['git','-C',str(root),*args],capture_output=True,check=True,timeout=15)
        if len(r.stdout)>4194304:raise ValueError('Inventory Git output limit')
        return r.stdout
    tracked={}
    for item in git('ls-files','--stage','-z','--',*roots).split(b'\0'):
        if not item:continue
        meta,name=item.split(b'\t',1);mode,blob,stage=meta.decode().split()
        if stage!='0':raise ValueError('Resolve index conflicts before inventory')
        tracked[name.decode()]={'index_blob':blob,'index_mode':mode}
    names=set(tracked)|{x.decode() for x in git('ls-files','--others','--exclude-standard','-z','--',*roots).split(b'\0') if x}
    if len(names)>4096:raise ValueError('Inventory file count limit')
    rows=[]
    for name in sorted(names):
        asset=Path(name).suffix.lower() in ASSETS
        row={'path':name,'tracking':'tracked' if name in tracked else 'untracked','kind':'asset' if asset else 'source-or-project-metadata','classification':'quarantined-pending-provenance-review','clean_handoff_eligible':False,'origin':'not-established','license':'not-assessed','exposure':'shared investigation/reconstruction repository; file-specific derivation not established',**tracked.get(name,{})}
        try:row.update(snapshot(safe(root,name)))
        except (OSError,ValueError) as error:row['inventory_error']=type(error).__name__+': '+str(error)
        if asset:row['attribution_status']='review-required'
        rows.append(row)
    return {'schema_version':1,'head':git('rev-parse','HEAD').decode().strip(),'declared_roots':roots,'files':rows,'counts':{'files':len(rows),'assets':sum(r['kind']=='asset' for r in rows),'inventory_errors':sum('inventory_error' in r for r in rows),'handoff_eligible':0},'repository_history_exposure':True,'independent_review_complete':False,'task_accepted':False,'limits':{'files':4096,'file_bytes':MAX_FILE,'git_seconds':15},'scope':'Declared current Cargo workspace, preview runtime/adapters and examples only; not a whole-repository or legal provenance certification.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);args=parser.parse_args()
    print(json.dumps(inventory(args.root),indent=2))
