# Agent descriptor and prepare-to-relaunch values

The pinned MessagingHost PrepareToRelaunchPayload decoder first requires
agentDescriptor, then retries agentIdentifier after any failure. Both attempts
use AgentDescriptor. That decoder first requires idAcrossRelaunches:String and
bundle:AgentDescriptor.Bundle. Any modern descriptor failure retries a flat
Bundle decoder on the entire original dictionary and uses an empty relaunch ID.
A valid modern descriptor wins over conflicting flat fields or legacy input.

Bundle decoding requires bundleID:String, then optional path:String. It does not
read discriminant. A present malformed path rejects; absent path succeeds.
Encoding always includes a discriminant computed from path presence: bundleID
when absent, pathAndBundleID when present, including an empty string path.
Bundle ID, relaunch ID and path are opaque strings. No identifier generation,
path lookup, bundle resolution, launch, preparation or authorization is implied.

Prepare encoding writes different representations under the two keys:
agentDescriptor is the full canonical descriptor; agentIdentifier is its bundle
only. This matters for interoperability with the legacy fallback. Outer
messageType is prepareToRelaunch (native internal MessageType 4/Content 2, not wire
integers). Outer payload errors propagate; common identifier validation remains
independent and precedes content fallback. The portable Error enum describes
final fallback failures; native NSError identity is not reproduced.

Static evidence: current MessagingHost SHA/UUID pinned; FoundationHost SHA also
checked. All 2,664 selected bytes independently matched LLVM disassembly, with
field descriptors, raw key getters, dictionary overload/import bindings,
required/optional String primitives, error edges, retry witnesses, empty String
construction, asymmetric encoder witnesses and outer dispatch/getter verified.
Complete Bundle decoder region has no discriminant unarchive. Source addresses:
Bundle decoder at 0x623c4, encoder at 0x62320; Descriptor decoder at 0x618b0, encoder at 0x617b0;
Prepare decoder at 0x65ef0, encoder at 0x65dbc; outer route at 0x5fdc8, getter at 0x5ea24. Raw
Apple disassembly/symbol listings remain local and are not publication artifacts.

Runtime evidence is deliberately scoped: 17 complete original dictionaries
passed through public Foundation serialization/casts plus original composition
of the recovered rules. 12 accept and 5 reject. This executes no private service
decoder, dispatcher or agent action. Controls cover modern/legacy/flat forms,
primary failure retry, nested failure retry, malformed modern ID with valid flat
bundle, modern precedence, ignored malformed discriminant, absent/empty path,
empty IDs, Unicode/control strings, missing keys and malformed nested values.

All 274 Rust tests pass, including three new tests covering every complete
control, canonical round trips, common identifier errors and actual native CLI
summary/binary modes. Actual Node WASI runs all 17 controls through the inspector
with explicit stdin/stdout handles, no filesystem preopens or inherited
environment. 12 canonical outputs match complete expected dictionaries with
integer/Bool type distinctions and pass public Foundation reparse; 5 failures
emit no binary output. Disposable replay reruns source checks, three new tests,
Foundation controls and actual WASI. Full 274-test output is retained separately.
No new verification failure occurred; expected malformed controls are not tool
failures. Public ServiceContent/Error enums add PrepareToRelaunch; exhaustive
matches must be updated. Inspector usage document includes normalization rules.

REA session identity was read once: 6.2.0 at the repository's retained server
path, no open target, Ghidra candidate reported available, alignment unknown
without an expected identity tuple. GhidraVibe inventory did not return before
bounded local orchestration cancellation; underlying request settlement was
not observed. No repeated inventory/import/restart loop. Offline source analysis
remained usable. Current native Canvas quarantine/owned cleanup requirements,
private decoder/agent preparation parity, refresh/rendering/provider lifecycle,
global resource settlement and both milestone contracts remain open.
