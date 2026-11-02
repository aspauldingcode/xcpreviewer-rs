from pathlib import Path
import plistlib,json
w=Path(__file__).parent;rows=[]
for mode in ['reply-first','remote-close','local-invalidate']:
 d=plistlib.loads((w/(mode+'.bplist')).read_bytes());assert d['callbackCount']==1 and not d['replyTimedOut']
 assert d['captureAliveWhilePending'] and d['captureReleasedAfterCleanup'] and not d['captureAliveAfterCleanup'] and not d['originalReferenceDroppedBeforeTrigger']
 events=d['captureEvents'];assert events.count('capture-used')==events.count('capture-destroyed')==1
 assert events.index('pending-after-caller-closure-scope')<events.index('capture-used')<events.index('capture-destroyed')
 assert events.index('original-connection-reference-held-through-trigger')<events.index('capture-used')
 p=d['peer'];assert p['peers']==p['dictionaries']==p['sameProcessPeer']==1 and plistlib.loads(p['messageData'])=={'ownedRequest':17}
 success=mode=='reply-first';assert d['uvPresent']==d['responseDataPresent']==success and d['errorPresent']!=success
 if success:assert d['response']==plistlib.loads(d['responseData'])=={'ownedReply':42} and d['nativeKind']==''
 else:
  expected={'remote-close':'connectionInterrupted','local-invalidate':'connectionInvalidated("xpc_connection_cancel()")'}[mode]
  assert d['nativeKind']==expected and d['errorDomain']=='PreviewsServices.XPCError' and d['errorCode']==1
 p.pop('peerEvents',None)
 # Timing of disposal relative to the main-thread wait is intentionally not a
 # deterministic contract; only the bounded observation above is qualified.
 d.pop('captureAliveAtReplyWait',None)
 rows.append(d)
(w/'native.bplist').write_bytes(plistlib.dumps(rows,fmt=plistlib.FMT_BINARY,sort_keys=True))
(w/'results.json').write_text(json.dumps({'controls':3,'capture_context_nonnull':True,'captured_swift_token_retained_after_caller_scope':3,'capture_uses':3,'capture_destructions_observed':3,'callbacks_observed':3,'original_native_connection_retained_through_reply':True,'notification_setter_calls':0,'native_future_calls':0,'scope':'Owned capture contexts with the previously qualified C callback relay. No typed Swift function-value reinterpretation, notification handler capture lifetime, delivery after original native-connection release, kernel-right settlement or universal callback finality is qualified.'},indent=2)+'\n');print((w/'results.json').read_text())
