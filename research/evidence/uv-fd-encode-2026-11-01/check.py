from pathlib import Path
import plistlib,json
w=Path(__file__).parent;rows=plistlib.loads((w/'native.bplist').read_bytes());assert len(rows)==2
for row in rows:
 assert row['uvWeakCleared'] and row['dataIsData'] and row['decoded']=={'ownedRequest':17} and row['fdReadbackMatches'] and row['fdReadbackBytes']==15
 if row['case']=='preserve-extra-fd':assert row['extraFDIdentityPreserved'] and row['rootEntryCount']==2 and not row['independentCollisionFDOwner']
 else:assert row['case']=='replace-data-fd' and row['rootEntryCount']==1 and row['independentCollisionFDOwner']
result={'native_controls':2,'uv_weak_cleared':2,'complete_payloads_equal':2,'extra_fd_identity_preserved':True,'post_uv_scope_descriptor_readbacks':2,'readback_bytes_per_control':15,'data_fd_replaced_by_data':True,'collision_readback_has_explicit_independent_owner':True,'scope':'Local actual UVPropertyList encoder and owned XPC dictionary; no IPC or native connection invocation. Extra descriptor survives under destination ownership. Collision readback relies on an explicit independent owner, not native disposal behavior. No final kernel-resource or Canvas parity claim.'}
(w/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
