# Single-selection candidate reads and delivered enablement writes

Recovered full singleSelection binding factory/read closure, isOn binding factory,
isEnabled keypath accessors, toggle thunks, group-state write thunk and setter:
3,124 instruction bytes match actual Mach-O bytes and independent LLVM output.
Exact defaultSelection, Binding factory/get/dynamicMember/set, selection/variant/ID,
Equatable and isEnabled getter/setter imports are asserted. Keypath relative pointers
resolve to exact accessors; toggle thunk resolves to group-state binding; writer
captures the complete group-state setter and its dictionary setValue/write calls.
The prior sealed row-read evidence supplies missing-state fallback semantics.

Factory availability requires a nonempty recursive default set, independently of
selection behavior style, enablement, stored matches or direct variant membership.
It captures the first default ID. The read scans stored Set order for a direct
variant ID match and returns that stored ID spelling; if no match it returns the
captured fallback. Recursive fallback may include unknown IDs or child defaults.
This does not select by root array order and does not match child-only variants.

The reconstruction exposes eligible candidate IDs and uses_defaults, plus an
explicit portable_value in deterministic decomposed-key order. It is a per-call
projection, not a retained binding/captured fallback or native Set-order parity.
Eight actual independent public Swift Set.first(where:) processes returned both
'a' and 'b' for two matching roots. Native order is therefore left unconstrained;
this is a public primitive observation, not an actual private Xcode getter call.
No candidate choice parity is claimed for several stored roots or defaults.
Inherited recursive-default representative differences also remain explicit.

The isOn binding projects a writable VariantGroupSettings.isEnabled keypath.
set_row_enabled models a delivered setter: read existing row/fallback, replace
only enablement, then store the complete state, including for equal Bool values.
It preserves selection and canonical dictionary-key spelling. A missing row is
installed by that delivered write; reads alone never install it. No claim whether
SwiftUI suppresses, batches, coalesces or delivers an actual equal-value UI event.
No native notifications, animation, persistence or process action performed.

The original bounded row-controls inspector validates a required group wire value,
optional settings (strict Bool isEnabled and String-array selection), optional
strict Bool requestedEnabled, then emits an original derived report. Optional
candidate fields exist only when defaults are nonempty. All configuration children
validate before calculation. Output previews cap eight stored/eight candidate IDs
at escaped256 scalars. This input/report is not Apple serialization.

329 Rust tests,26 original public Swift/Foundation compositions (20 accept/six
reject),46 actual WASI invocations (26 canonical+20 summaries),20 Foundation
reparses pass. Complete type-sensitive values and byte-identical bounded summaries
agree. Three new tests cover full calculations, read immutability, delivered writes,
canonical key preservation and CLI output. Disposable source/focused/composition/
WASI replay and eight eligible-ID Set probes pass. Full test output retained.

REA identity fields match the prior pinned tuple; closed session/provider binding
null. Alignment field remains unknown without supplied expected fields; explicit
recorded-field comparison used. No new tool/verification failure or Ghidra/import
retry. Raw Apple disassembly remains ignored/local. Private bindings/lifetimes,
selection order, UI events, transport, rendering, refresh/provider lifecycle and
global resource settlement are unverified. Both milestone contracts remain open.

Next: connect reconstructed row controls to application state; prioritize Pipeline
previewRequests/content-override mapping and remaining transport/resource semantics.
Actual native lifecycle/rendering/provider observations are still required.
