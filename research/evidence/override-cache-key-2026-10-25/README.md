# Content-override cache-key identity

Located Pipeline EditorSettings.previewRequests6ee3c..70b58 (7,452 bytes), with
verified direct effectiveGroupsAndOverrides call6f610->2b7988. Full constructor
remains partially analyzed and unimplemented; raw local disassembly is retained.
Followed the capabilities path to the content-override cache's identity boundary.

Recovered complete ContentOverrideKey hash/equality and override-array equality:
876 Pipeline bytes, plus56 MessagingHost scalar witness/thunk bytes and4 consumer
callsite bytes=936 bytes independently matched against actual Mach-O/LLVM output.
Reflection fields are contentCategory/requestedOverrides. Actual imported category/
override Equatable/Hashable conformances and metadata are pinned. Named scalar
witness aliases share36b24->36388->366b0, delegating to Swift String comparison.
Key equality compares category first, then array counts and ordered positionwise
IDs. Hash combines category, array count and every ordered override. Duplicate
multiplicity, ordering, empty arrays/IDs, case and compatibility distinctions matter.
Category and IDs use qualified canonical Unicode String equality.

Added immutable ContentOverrideCacheKey via RequestContentOverridePayload::cache_key.
It normalizes category and each ordered ID with the already-qualified Unicode16
policy. It leaves original payload bytewise equality, wire spelling, order and
multiplicity unchanged. Rust-local Hash/Eq support portable HashMap memoization;
native Swift hash bit values are deliberately not reproduced. No actual cache
fetch, async task coalescing, cancellation, error retention, invalidation, persistence
or lifecycle behavior is implemented or claimed by this key-only contract.

The bounded override-cache-keys inspector validates an entire array of existing
content-override payload dictionaries, then reports first-representative indices
and unique-key count. This batch/report is original tooling, not Apple wire/cache
serialization. Summary shows at most eight indices. Malformed late entries produce
no partial output. Existing wire codecs remain unchanged.

332 Rust tests,26 original public Swift Hashable/Dictionary/Foundation compositions
(20 accepts/six rejects),46 actual WASI invocations (26 canonical+20 summaries) and
20 Foundation reparses pass. Complete type-sensitive reports and byte-identical
summaries agree. Three new tests cover full equivalence classes, immutable wire
values, Hash/Eq consistency and bounded CLI behavior. Disposable source/focused/
public-composition/WASI replay passes; full332-test output retained separately.
Native controls use an original Swift String/[String] Hashable key and Dictionary,
not the shipped private key/cache. Unicode16 qualification remains inherited.

Exploratory parser failed on a blank objdump line; corrected address-line filtering
succeeded. A generic conformance descriptor had a nil static witness-table pattern;
initial integer conversion failed, so no guessed dereference/runtime ABI followed.
Used named exact witness aliases and direct thunk targets instead. Guessed inventory
filenames did not exist; actual symbols were obtained with bounded nm. These failures
are preserved, not treated as native target behavior or access denials.

REA identity fields match the pinned tuple; closed session/provider binding null;
server alignment remains unknown without expected fields, with explicit identity
comparison recorded. No repeated Ghidra/import failure loop, Xcode MCP, native UI
process action or system change. Raw Apple symbols/disassembly remain ignored/local.
Both milestone contracts remain open. Next: finish previewRequests canvas-mode,
associated-group filtering, request fields and content-override service mapping;
recover async cache coalescing/error/invalidation and native transport/resource
lifecycle before claiming full request or resource parity.
