# Variant-discovery and content-override request values

Recovered two outer service request shapes. `variants` decodes
RequestPreviewVariantsPayload: required contentCategory and optional
contentOverride. `contentOverride` decodes RequestContentOverridePayload:
required contentCategory and required requestedOverrides array. Empty array
is valid; missing array rejects. Order, duplicate strings and empty strings
remain intact. A malformed present optional override propagates an error.

ContentCategory and ContentOverride are open String wrappers. Exact native
symbol definitions and copy-only raw initializers establish that strings are
not restricted to known enum cases. Unknown future names and empty strings are
retained; this does not establish that an agent understands or honors them.
These request types are distinct from PreviewVariantsPayload(groups) and
ContentOverridePayload(contentOverride). Reply parsing/application, discovery
execution and override effects remain outside this implementation.

The native/WASI inspector supports both new kinds. Default override summary
reports total array count and at most eight strings, each independently escaped
and capped at 256 Unicode scalars. Canonical binary stdout retains the complete
ordered array. Common envelope identifier validation remains separate and
precedes content decoding. Both payload error paths propagate; neither uses
the tolerant capabilities fallback. No identifiers or requests are sent.

Source evidence: installed MessagingHost SHA/UUID and FoundationHost SHA pinned.
2,192 selected bytes independently matched LLVM, covering raw key getters,
request encoders/decoders, required/optional imports, wrapper property-list
witnesses, nonfailable String-copy initializers, exact array metadata/conformance
cache symbols, outer request dispatch and payload getters. Native MessageType
12/13 and Content 10/11 are internal tags, not wire integers. Actual indirect
symbol bindings are checked instead of trusting LLVM's folded alias labels.
The array path uses the ContentOverride wrapper conformance, not the unrelated
DynamicLoadablePreviewProduct alias displayed at the folded helper address.
Raw Apple disassembly and symbol tables remain local ignored artifacts.

Runtime evidence: 21 original dictionaries pass public Foundation casts and
serialization plus original source-guided request composition. Ten accept and
11 reject. Controls include missing/wrong category, absent/empty/unknown single
override, malformed single override, required empty/ordered/duplicate/Unicode
arrays, malformed array and elements, unknown fields, and reply-shaped or
wrong-namespace payloads. All 277 Rust tests pass, including three new complete
control/round-trip/error/identifier/CLI tests. Actual Node WASI performs 21
canonical executions and ten accepted summary executions (31 total), with no
filesystem preopens or inherited environment. Accepted canonical dictionaries
match complete type-sensitive expected values and pass ten public Foundation
reparses. Rejected cases emit no binary output. Accepted summaries match native
bytes. Disposable replay repeats source checks, three new tests and the entire
Foundation/WASI comparison; full 277-test output is retained separately.
Public Foundation operations and original composition do not call private
service decoders, discover variants or apply overrides.

A bounded compiler-checked private decoder route was attempted: framework
inventory contains no Swift module/interface files, and `swiftc -typecheck`
with the shipped framework search path reports `no such module
'PreviewsMessagingHost'`. The probe does not link or execute a private decoder.
No guessed Swift ABI call was substituted. Other module locations or future
compiler interfaces remain unqualified. Source analysis/implementation remained
usable, so no user action was required.

Two source-verifier assumptions failed and were corrected against exact native
bindings: the String PropertyListType conformance uses the full
PreviewsFoundationHost module name, and the array metadata cache suffix is
case-sensitive `Md`, not `MD`. Initial verifier and failure records retained.
No product-code change was needed to hide either mismatch. Latest REA identity
was checked using the retained expected package/path/catalog tuple; provider
readiness is separate. No repeat Ghidra inventory/import/status loop.

API: ServiceContent adds Variants and ContentOverride; service_envelope::Error
adds ContentRequest. Exhaustive Rust matches must update. Native private
request/reply/action parity, launch/relaunch/update kinds, Canvas lifecycle,
refresh/rendering/provider cleanup, global resource settlement and both
milestone contracts remain open.
