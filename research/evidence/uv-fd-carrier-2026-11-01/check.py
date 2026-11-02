from pathlib import Path
import plistlib,json
w=Path(__file__).parent;rows=[]
for case in ['extra-fd','collision']:
 d=plistlib.loads((w/(case+'.bplist')).read_bytes());assert d['case']==case and d['senderUVWeakCleared'] and d['senderReleaseGatePassed'] and d['sameProcessPeer'] and d['connections']==d['messages']==1 and d['nativeProjection']=={'ownedRequest':17}
 if case=='extra-fd':assert d['descriptorPresent'] and d['readbackMatches'] and d['readbackBytes']==14 and d['receivedRootCount']==2
 else:assert not d['descriptorPresent'] and not d['readbackMatches'] and d['readbackBytes']==0 and d['receivedRootCount']==1
 rows.append(d)
(w/'native.bplist').write_bytes(plistlib.dumps(rows,fmt=plistlib.FMT_BINARY,sort_keys=True))
result={'controls':2,'native_encoder_to_sdk_to_native_decoder':2,'complete_native_payload_equal':2,'source_uv_weak_cleared_before_receiver_projection':2,'receiver_extra_fd_duplicate_and_read_after_sender_scope':True,'receiver_fd_readback_bytes':14,'collision_descriptor_not_forwarded':True,'same_process_peer':True,'scope':'Owned anonymous SDK IPC in one process; real FD import/read after sender local scope exit and UV weak clearing. No sender-process death, exact SDK-internal sender-object release, native connection/Canvas receiver route, cross-process parity or final kernel-resource settlement.'}
(w/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
