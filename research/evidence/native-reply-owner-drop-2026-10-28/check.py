from pathlib import Path
import plistlib,json
w=Path(__file__).parent;rows=[]
for mode in ['reply-first','remote-close']:
 d=plistlib.loads((w/(mode+'.bplist')).read_bytes())
 assert d['callbackCount']==1 and not d['replyTimedOut']
 assert d['originalReferenceDroppedBeforeTrigger'] and d['nativeAliveAfterOwnerDrop'] and not d['nativeAliveAfterCleanup']
 assert d['captureAliveWhilePending'] and d['captureReleasedAfterCleanup'] and not d['captureAliveAfterCleanup']
 events=d['captureEvents'];assert events.count('capture-used')==events.count('capture-destroyed')==1
 assert events.index('pending-after-caller-closure-scope')<events.index('original-connection-reference-dropped-before-trigger')<events.index('capture-used')<events.index('capture-destroyed')
 peer=d['peer'];assert peer['peers']==peer['dictionaries']==peer['sameProcessPeer']==1 and not peer['receiveTimedOut']
 assert plistlib.loads(peer['messageData'])=={'ownedRequest':17}
 success=mode=='reply-first';assert d['uvPresent']==d['responseDataPresent']==success and d['errorPresent']!=success
 if success:assert d['response']==plistlib.loads(d['responseData'])=={'ownedReply':42} and d['nativeKind']==''
 else:assert d['nativeKind']=='connectionInterrupted' and d['errorDomain']=='PreviewsServices.XPCError' and d['errorCode']==1
 peer.pop('peerEvents',None);d.pop('captureAliveAtReplyWait',None);rows.append(d)
(w/'native.bplist').write_bytes(plistlib.dumps(rows,fmt=plistlib.FMT_BINARY,sort_keys=True))
results={'controls':2,'original_reference_dropped_before_trigger':2,'native_connection_weak_alive_after_owner_drop':2,'native_connection_weak_cleared_by_cleanup':2,'capture_contexts_retained_after_caller_scope':2,'capture_uses':2,'capture_destructions_observed':2,'callbacks_observed':2,'notification_setter_calls':0,'scope':'Actual native connection remains alive after caller reference release while reply is pending, then weak reference clears during bounded cleanup. This does not demonstrate a callback after native object destruction, exact native deinit timing, final kernel-right settlement, or universal callback finality.'}
(w/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
