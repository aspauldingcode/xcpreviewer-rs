"""Verify actual owned native token-copy controls and context/FD lifetime boundaries."""
from pathlib import Path
import argparse,json
MODES=['owned-copy-abi','copy-invalidate','copy-cancel','copy-drop-both','copy-owner-loss','copy-inflight']

def verify(root):
    root=Path(root);result={};previous_end=None
    for mode in MODES:
        status=json.loads((root/('native-'+mode+'.result.json')).read_text());rows=[json.loads(x) for x in (root/('native-'+mode+'.stdout')).read_text().splitlines()]
        assert status['code']==0 and not status['timeout'] and rows[0]['event']=='native-ready' and rows[0]['pid']==status['pid']
        assert [v['seq'] for v in rows]==list(range(1,len(rows)+1)) and all(a['time_ns']<=b['time_ns'] for a,b in zip(rows,rows[1:]))
        if previous_end is not None:assert rows[0]['time_ns']>previous_end
        previous_end=rows[-1]['time_ns'];assert all(isinstance(v['thread_id'],int) and v['thread_id']>0 for v in rows)
        assert rows[-1]['event']=='pass' and rows[-1]['mode']==mode
        events=[v['event'] for v in rows]
        def one(event):
            found=[v for v in rows if v['event']==event];assert len(found)==1,event;return found[0]
        def pos(event):return one(event)['seq']
        created=one('probe-created');dead=one('probe-deinit');assert created['fd']==dead['fd'] and dead['close_result']==0
        callbacks=[v['name'] for v in rows if v['event']=='callback'];expected=[mode] if mode in ['copy-invalidate','copy-drop-both','copy-inflight'] else []
        assert callbacks==expected and rows[-1]['callbacks']==expected
        if mode=='owned-copy-abi':
            assert one('owned-original-destroyed-copy-live')['context_alive'] and one('owned-original-destroyed-copy-live')['fd_open']
            assert one('owned-copy-abi-cleanup')['context_released'] and one('owned-copy-abi-cleanup')['fd_closed']
            assert pos('probe-created')<pos('owned-original-destroyed-copy-live')<pos('probe-deinit')<pos('owned-copy-abi-cleanup')
        else:
            copy=one('token-copy-complete');assert copy['vwt_slot_byte_offset']==16 and copy['copy_image']=='PreviewsFoundationHost' and copy['copy_function_image_offset']==0x12a0ec
            assert one('registered')['has_token'] and pos('registered')<copy['seq']
            assert events.count('token-destroy-begin')==events.count('token-destroy-end')==2
            assert one('copy-control-cleanup')['context_released'] and one('copy-control-cleanup')['fd_closed']
            destroys=[v['seq'] for v in rows if v['event']=='token-destroy-end']
            if mode=='copy-invalidate':
                alive=one('original-token-dropped-copy-kept');assert alive['context_alive'] and alive['fd_open']
                assert destroys[0]<alive['seq']<pos('invalidate-begin')<pos('callback')<pos('probe-deinit')<pos('invalidate-end')<pos('cancel-begin')<destroys[1]
            elif mode=='copy-cancel':
                done=one('original-cancelled-copy-kept');assert done['context_released'] and done['fd_closed']
                begins=[v['seq'] for v in rows if v['event']=='cancel-begin'];ends=[v['seq'] for v in rows if v['event']=='cancel-end'];assert len(begins)==len(ends)==2
                assert begins[0]<pos('probe-deinit')<ends[0]<done['seq']<begins[1]<ends[1]<pos('invalidate-begin')<pos('invalidate-end')<destroys[0]<destroys[1]
            elif mode=='copy-drop-both':
                alive=one('both-tokens-dropped-context-live');assert alive['context_alive'] and alive['fd_open']
                assert destroys[1]<alive['seq']<pos('invalidate-begin')<pos('callback')<pos('probe-deinit')<pos('invalidate-end')
            elif mode=='copy-owner-loss':
                gone=one('owner-lost-copies-kept');assert gone['owner_released'] and gone['context_released'] and gone['fd_closed']
                assert pos('handle-release-begin')<pos('probe-deinit')<pos('handle-release-end')<gone['seq']<next(v['seq'] for v in rows if v['event']=='cancel-begin')<destroys[0]<destroys[1]
            elif mode=='copy-inflight':
                callback=one('callback');assert callback['probe_strong_local_created'] is False
                held=one('copies-dropped-callback-blocked');assert held['context_alive'] and held['fd_open'] and held['thread_id']!=callback['thread_id']
                assert pos('callback-blocked')<pos('cancel-begin')<pos('cancel-end')<destroys[0]<destroys[1]<held['seq']<pos('callback-unblocked')<pos('probe-deinit')<pos('invalidate-end')<pos('copy-control-cleanup')
                assert callback['thread_id']==dead['thread_id']==one('invalidate-end')['thread_id']
        result[mode]='native scoped assertions passed'
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);print(json.dumps(verify(p.parse_args().directory),indent=2))
