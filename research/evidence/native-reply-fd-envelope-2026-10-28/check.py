from pathlib import Path
import plistlib,json,re
w=Path(__file__).parent;rows=[]
for case in ['extra-fd','fd-as-data']:
 d=plistlib.loads((w/(case+'.bplist')).read_bytes());p=d['peer']
 assert d['callbackCount']==1 and not d['replyTimedOut'] and d['captureAliveWhilePending'] and d['captureReleasedAfterCleanup'] and not d['captureAliveAfterCleanup']
 assert p['descriptorPrepared'] and p['descriptorOriginalClosed'] and p['descriptorAsData']==(case=='fd-as-data')
 assert p['peers']==p['dictionaries']==p['sameProcessPeer']==1 and plistlib.loads(p['messageData'])=={'ownedRequest':17}
 assert d['captureEvents'].count('capture-used')==d['captureEvents'].count('capture-destroyed')==1
 assert not re.search('0x[0-9a-fA-F]+',d['nativeKind']+d['errorDescription'])
 if case=='extra-fd':assert d['uvPresent'] and not d['errorPresent'] and d['response']==plistlib.loads(d['responseData'])=={'ownedReply':42}
 else:assert not d['uvPresent'] and not d['responseDataPresent'] and d['errorPresent'] and d['nativeKind'].startswith('invalidType(') and '<fd:' in d['nativeKind'] and d['errorDomain']=='PreviewsServices.XPCError' and d['errorCode']==1
 p.pop('peerEvents',None);d.pop('captureAliveAtReplyWait',None);d['case']=case;rows.append(d)
(w/'native.bplist').write_bytes(plistlib.dumps(rows,fmt=plistlib.FMT_BINARY,sort_keys=True))
(w/'results.json').write_text(json.dumps({'controls':2,'owned_descriptor_validated_before_send':2,'original_descriptor_closed_before_send':2,'extra_descriptor_projected_dictionary_equal':True,'descriptor_as_data_native_invalid_type':True,'callbacks_observed':2,'capture_destructions_observed':2,'scope':'Actual native reply-to-UVPropertyList projection. Extra root FD does not appear in observed complete dictionary/data; FD-valued data returns native invalidType. No receiver FD duplication/read, resource ownership API, exact final descriptor/Mach-right settlement or full protocol/resource parity is established.'},indent=2)+'\n');print((w/'results.json').read_text())
