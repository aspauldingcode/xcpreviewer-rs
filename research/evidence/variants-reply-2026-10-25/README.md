# Grouped variants payload values

Recovered PreviewVariantGroup requires an open String ID first, then optional
associatedGroupIDsArray, optional overridesConfiguration and optional
variantsConfiguration. Missing associations become an empty Set; present invalid
arrays/elements or malformed optional configurations propagate errors. The
similarly named associatedGroupIDs field is not the wire key and is ignored.
Group IDs use the same raw String wrapper/equality profile as other opaque IDs.
Canonical output always writes id and the association array, omitting absent
configurations. Nested configurations reuse complete qualified value codecs,
including existing legacy normalization and recursive override input boundaries.

PreviewVariantsPayload requires ordered groups:[PreviewVariantGroup]. Empty
arrays are valid, missing groups reject, duplicate groups/IDs and order remain
intact. A bad group rejects the whole payload and retains its index/cause.
Association IDs form a Unicode16 canonical set, retaining first spelling and
using deterministic NFD-key output order. Self/unresolved links are retained;
no graph resolution, filtering or selection policy is imposed. The existing
VariantIdSet is reused through the AssociatedGroupIds alias because both IDs
have the qualified raw String profile. Other String equality remains unchanged.

2,228 selected source bytes independently match LLVM. Pinned current image
SHA/UUID, complete group getter/encoder/decoder, group ID raw constructor,
required/optional calls/error branches, actual empty-array storage binding,
array-to-Set constructor, Set sequence copy, exact configuration witnesses,
reply encoder/decoder and precise group/group-ID array metadata caches checked.
Actual conformance arguments resolve misleading folded generic helper labels.
Raw Apple disassembly stays local ignored files. Initial bounded getter
projection stopped at ORR-immediate2; LLVM also identified CSINC. The exact
bounded instruction subset was extended and all four keys matched metadata.
This tooling failure is retained; no codec behavior correction was needed.

The inspector adds explicit group and variants-reply modes. variants-reply is
PreviewVariantsPayload only: it does not decode a transport reply envelope,
correlate a request, prove reply success, register peer dispatch or apply/render
contents. Existing request handling remains separate in inspect-service-message.
Summaries show at most four groups/four association IDs per group, optional
configuration titles, total/shown counts and individual escaping/256-scalar
limits. Configuration trees are not expanded in summaries. Canonical output
retains every complete supported group/configuration.

All302 Rust tests pass, including four new complete native expected value/
round-trip, validation order/index, opaque association/inherited collision and
actual CLI/bounded-summary tests.32 original public Foundation casts/dictionary
compositions with public Swift Set/String yield16 accepts and16 rejects. Controls
cover minimal/empty/unknown IDs, missing/empty/duplicate Unicode associations,
ignored wrong-key spelling/unknown fields, both nested configuration forms,
legacy variants, ordered duplicate groups, nested failures and long/many values.
Actual WASI executes32 canonical cases plus16 accepted summaries (48 invocations),
explicit standard I/O, no filesystem preopens/inherited environment. Complete
accepted dictionaries agree type-sensitively and16 WASI outputs pass Foundation
reparse. Accepted summaries match native Rust bytes. Disposable replay repeats
source/four focused tests/all Foundation/WASI comparisons; full302-test output
retained separately. Public compositions do not invoke private Apple decoders.

Native randomized Set/dictionary order, Unicode versions outside the qualified
runtime, ambiguous raw canonical-equivalent child keys, direct-value recursion
limits and sibling dictionary error-order differences remain inherited explicit
boundaries. The preceding tree evidence separately records public native bridge
acceptance versus portable rejection for ambiguous raw inputs; those unchanged
native probes were not rerun. This component does not erase that difference.
REA package/path/catalog align; no target open/provider binding. No repeated
private module/Ghidra inventory attempt or private ABI guess.

Dependency graph now marks group and payload as scoped typed-value codecs with
the inherited raw-key restriction. Transport correlation/dispatch/actions,
default-selection aggregation, native Canvas interaction/refresh/rendering/
provider lifecycle and global resource settlement remain open. Both milestone
contracts remain incomplete.
