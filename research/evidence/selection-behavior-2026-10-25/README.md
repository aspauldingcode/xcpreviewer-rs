# Selection behavior routing

Recovered SelectionBehavior as an enum value codec over the already qualified
single-select and multi-select configurations. A required closed String
`discriminant` is decoded first: `singleSelect` or `multiSelect`. Only its
matching configuration is required and decoded. An inactive configuration is
ignored, even when present and malformed. Active failures propagate without
retrying the inactive branch. Unknown/wrong-case/empty discriminants reject
even if both configuration payloads are otherwise valid. Canonical output
contains exactly the discriminator and active normalized configuration.
Portable nested errors retain existing single/multi causes, not native NSError
identity. No variant availability validation or selection/application occurs.

1,264 selected bytes independently match LLVM: current pinned image SHA/UUID,
full raw key and discriminant getters, two-case failable String initializer,
complete selected-branch decoder, both encoder closures, required unarchive
calls, error propagation and exact single/multi conformance witnesses. The
String lookup helper is resolved by its actual import binding, not a folded
label. Native private Swift decoders are not invoked.

A separately checked pending dependency is important: the parent field
childVariantConfigurations uses the exact conformance for
Dictionary<PreviewVariant.ID,PreviewOverridesConfiguration>, recursively. It is
not an ordered child array and does not contain PreviewVariantsConfiguration.
The optional field call and actual dictionary witness are pinned. Canonical
key collisions, representative handling, recursive failures/defaults and parent
encoding need further analysis before a full override codec is implemented.
No opaque or partial parent/group decoder is substituted.

The inspector adds explicit selection-behavior mode, reporting the active tag
and either the single style/default ID or the bounded multi-default set. Each
ID is escaped and capped at256 Unicode scalars with original byte/truncation
counts; at most eight multi IDs are shown with total/shown counts. Canonical
binary output retains the complete active payload. Multi-set output reuses the
previously documented deterministic NFD-key order and retained spellings; native
randomized Set byte order is not reproduced. Existing modes remain available.

All294 Rust tests pass, including three new complete-value/round-trip,
required/discriminator/active-error and actual CLI/summary tests.26 original
public Foundation dictionary/cast compositions (including public Swift Set for
active multi defaults) yield11 accepts and15 rejects. Controls cover both active
branches, malformed inactive data, valid inactive data with missing/invalid
active payloads, Unicode duplicate normalization, empty values, unknown fields,
closed enum errors and long/many defaults. Actual WASI executes26 canonical
cases plus11 accepted summaries (37 invocations), with explicit standard I/O,
no filesystem preopens and no inherited environment. Accepted output matches
complete type-sensitive expected dictionaries and11 WASI outputs pass public
Foundation reparse. Native/WASI summaries match bytes. Disposable replay repeats
source checks, three focused tests and all Foundation/WASI comparisons; full
294-test output is retained separately. No new verification failures occurred.

These are original source-guided compositions and portable implementations,
not private framework decoder or native Canvas runtime parity. Unicode-version
qualification/failures and the explicit set ordering policy remain in sealed
predecessor evidence; unchanged native Unicode probes were not rerun. Private
module import and unsettled Ghidra inventory limitations were not retried; no
private ABI guess. REA package/path/catalog align; no target open/provider
binding null. Raw Apple disassembly stays local ignored files.

Dependency graph now includes implemented SelectionBehavior with both payload
dependencies and the pending recursive override dictionary. Full parent/groups,
native dispatch/actions, Canvas interaction/selection/rendering/refresh/provider
lifecycle and global resource settlement remain open. Both milestone contracts
remain incomplete.
