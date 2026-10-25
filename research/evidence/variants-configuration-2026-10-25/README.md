# Sectioned variant configuration values

Recovered PreviewVariantsConfiguration and its Section codec as the next
prerequisite for complete grouped variants. Configuration requires title:String,
then sections:[Section]. Section first accepts optional title:String, then
requires variants:[PreviewVariant]. Empty arrays are valid but absence is not a
default empty array. A present malformed optional section title rejects. Empty
String title remains present. Order, duplicate sections and duplicate variant
IDs remain intact; no uniqueness, selection or grouping policy is imposed.

Nested variants reuse the previously verified complete individual entry codec,
including modern effects versus legacy fallback and canonical legacy effect
output. Canonical configuration/section output omits unknown fields and absent
section title. Portable nested errors retain section and variant indexes with
original portable causes; native NSError identity is not reproduced. Failure
propagates rather than dropping malformed sections or variants.

inspect-content-result adds explicit configuration and section modes. Default
summaries show at most four sections and four variant IDs/display names per
shown section, with total/displayed counts. Every String is independently
escaped and capped at 256 Unicode scalars. Canonical binary stdout retains all
sections and variants. These modes do not select a variant, decode a complete
grouped reply, resolve an effect or render it. Existing variant/override modes
remain available. See the updated usage document.

Source evidence: current MessagingHost SHA/UUID and FoundationHost SHA pinned.
1,312 selected bytes independently matched LLVM, including full raw key getters,
canonical encoder closures and complete configuration/section decoders. Required
versus optional String calls, required array calls, error branches, exact Section
and PreviewVariant metadata/conformance-cache symbols, and generic dictionary
encoder imports checked. Native folded helper labels are not treated as element
type authority: exact nlist symbols and witness address arguments establish the
actual element types. Raw Apple disassembly/symbols remain local ignored files.

Runtime evidence: 24 complete original dictionaries pass public Foundation
casts/serialization plus original composition of these source-derived rules.
Eleven accept and thirteen reject. Controls include empty required arrays,
required versus absent/empty optional titles, ordered and duplicate sections and
variants, unknown fields, Unicode/control text, malformed sections and nested
variants, title validation order and nested legacy normalization. Public
Foundation/original composition does not invoke private configuration decoders.

All 284 Rust tests pass. Three new tests cover complete expected values and
round trips, required/optional/error ordering and nested indexes, both actual
CLI modes and bounded nested summaries. Actual Node WASI performs all 24
canonical cases plus eleven accepted summaries (35 invocations), no filesystem
preopens or inherited environment, explicit standard-I/O handles only. Accepted
canonical dictionaries match complete type-sensitive expectations and eleven
outputs pass public Foundation reparse. Accepted summaries match native bytes;
rejected controls emit no binary stdout. Disposable replay repeats source
checks, focused tests and all Foundation/WASI comparisons; full 284-test output
is retained separately. No new verification failures occurred.

Dependency graph now records Section and PreviewVariantsConfiguration as scoped
codec implementations with direct pinned type/witness provenance. Override
selection configuration, PreviewVariantGroup and full PreviewVariantsPayload
remain pending. No partial group codec is silently substituted. REA identity
checked against expected package/path/catalog; provider readiness remains
separate. No repeated Ghidra inventory or private Swift import attempts.

Private decoder parity, complete grouped/selection configuration/reply behavior,
actual UI selection/rendering/refresh/provider lifecycle and global resource
settlement remain open. Both milestone contracts remain incomplete.
