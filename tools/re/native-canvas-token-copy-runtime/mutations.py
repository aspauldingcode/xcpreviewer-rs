"""Synthetic semantic corruptions of retained native token-copy traces."""
from pathlib import Path
import json,tempfile,shutil
from verify import verify,MODES
source=Path(__file__).resolve().parents[3]/'research/evidence/canvas-runtime-token-copy-2026-11-03/b'
results=[]
for case in ['owned-abi-live','wrong-copy-entry','cancel-releases-context','drop-both-retention','owner-not-released','callback-strong-local','wrong-deinit-thread','missing-token-destroy']:
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)
        for mode in MODES:
            for suffix in ['.stdout','.result.json']:shutil.copyfile(source/('native-'+mode+suffix),p/('native-'+mode+suffix))
        mode={'owned-abi-live':'owned-copy-abi','wrong-copy-entry':'copy-invalidate','cancel-releases-context':'copy-cancel','drop-both-retention':'copy-drop-both','owner-not-released':'copy-owner-loss','callback-strong-local':'copy-inflight','wrong-deinit-thread':'copy-inflight','missing-token-destroy':'copy-invalidate'}[case]
        path=p/('native-'+mode+'.stdout');rows=[json.loads(x) for x in path.read_text().splitlines()]
        def row(event):return next(v for v in rows if v['event']==event)
        if case=='owned-abi-live':row('owned-original-destroyed-copy-live')['context_alive']=False
        elif case=='wrong-copy-entry':row('token-copy-complete')['copy_function_image_offset']=0
        elif case=='cancel-releases-context':row('original-cancelled-copy-kept')['context_released']=False
        elif case=='drop-both-retention':row('both-tokens-dropped-context-live')['fd_open']=False
        elif case=='owner-not-released':row('owner-lost-copies-kept')['owner_released']=False
        elif case=='callback-strong-local':row('callback')['probe_strong_local_created']=True
        elif case=='wrong-deinit-thread':row('probe-deinit')['thread_id']=row('copies-dropped-callback-blocked')['thread_id']
        elif case=='missing-token-destroy':
            rows.pop(next(i for i,v in enumerate(rows) if v['event']=='token-destroy-end'))
            for index,v in enumerate(rows,1):v['seq']=index
        path.write_text(''.join(json.dumps(v)+'\n' for v in rows))
        try:verify(p)
        except (AssertionError,KeyError,StopIteration):results.append({'case':case,'rejected':True})
        else:raise AssertionError('Accepted corrupted evidence: '+case)
print(json.dumps({'kind':'synthetic-evidence-reader-controls','results':results},indent=2))
