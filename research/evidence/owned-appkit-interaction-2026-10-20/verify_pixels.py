"""Independent byte/receipt verifier for this profile-pinned owned AppKit control."""
from pathlib import Path
import json,hashlib
PROFILE='86dc86f10f233708f83c37128a89abaf6a7597c87b92cf039b4fe81677990a36'
RAW={'before.bin':(234,51,35,255),'repeat.bin':(234,51,35,255),'after.bin':(0,0,245,255),'after-repeat.bin':(0,0,245,255)}
EXPECTED={**RAW,**{f'srgb-{n}.bin':((255,0,0,255) if n<2 else (0,0,255,255)) for n in range(4)}}
def verify_buffers(buffers,icc):
    assert hashlib.sha256(icc).hexdigest()==PROFILE
    assert set(buffers)==set(EXPECTED)
    for name,pixel in EXPECTED.items():
        assert len(buffers[name])==38400 and buffers[name]==bytes(pixel)*9600
    assert buffers['before.bin']!=buffers['after.bin']
    return sum(map(len,buffers.values()))
def verify_receipts(result,cleanup):
    assert result['private_event_decoded'] is True and result['clicks']==1
    assert result['all_event_bytes_roundtrip_equal']==256
    assert result['baseline_repeat_equal'] and result['after_repeat_equal'] and result['changed_frame']
    assert result['event_posted_to_system'] is False and result['native_canvas_protocol_observed'] is False
    assert result['owned_visible_windows_remaining']==0 and cleanup['owned_windows_remaining']==0
    assert cleanup['fresh_queries']>=1
if __name__=='__main__':
    import sys
    root=Path(sys.argv[1]);buffers={n:(root/n).read_bytes() for n in EXPECTED};icc=(root/'capture.icc').read_bytes();count=verify_buffers(buffers,icc)
    assert (root/'event-reference.bin').read_bytes()==(root/'event-decoded.bin').read_bytes() and (root/'event-reference.bin').stat().st_size==256
    result=json.loads((root/'interaction.stdout').read_text());cleanup=json.loads((root/'window-cleanup.json').read_text());verify_receipts(result,cleanup)
    rejected=0
    for name,mutant in [('after.bin',bytes([1])+buffers['after.bin'][1:]),('srgb-3.bin',buffers['srgb-3.bin'][:-1]),('repeat.bin',buffers['after.bin'])]:
        try:verify_buffers({**buffers,name:mutant},icc)
        except AssertionError:rejected+=1
    try:verify_receipts(result,{**cleanup,'owned_windows_remaining':1})
    except AssertionError:rejected+=1
    assert rejected==4
    print(json.dumps({'independent_bytes_equal':count,'corrupted_pixel_length_baseline_cleanup_controls_rejected':rejected,'capture_icc_sha256':PROFILE}))
