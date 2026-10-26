# Grid request override calculation

Pipeline EditorSettings.previewRequests calls effectiveGroupsAndOverrides, then
its grid-tag branch excludes a tuple if group IDs compare equal or either group's
associatedGroupIDs contains the other ID. Both membership loops use Group.ID
Hashable/Equatable. Surviving tuples append in input order; their override arrays
flatten in order with duplicates. Empty effective arrays yield empty overrides.
1,812 selected source bytes match LLVM/Mach-O exactly. This is a scoped branch
analysis, not recovery or runtime validation of the complete 7,452-byte method.
Existing key/String Unicode 16 qualification and group/selection codecs are
inherited through the predecessor evidence chain.

Original grid_request_overrides computes effective groups, excludes the grid ID
and either direct association, then flattens. The supplied complete grid group is
the CanvasMode.grid payload; it need not occur among discovered groups. Do not
replace it with an equal-ID discovered group or follow transitive associations.
Existing missing/disabled settings, configuration, direct selection and one-level
child rules remain in force. Input state is unchanged; result variants are owned.
Capability fallback, mode selection, grid variant enumeration, complete request
fields and execution are outside this API's contract.

The grid-request-overrides inspector accepts original groups/settings/gridGroup
input, validates it completely, and emits a complete Variant array. gridGroupID
is unused here. Summary is bounded to eight IDs, each 256 escaped scalars. It is
not an Apple wire request, transport implementation or native UI action.

338 Rust tests pass. Three new tests compare complete derived values, preserve
inputs/owned output independence, and check CLI canonical/summary/rejection paths.
32 original public Swift Set/String/Foundation compositions (26 accepts/six
rejects),58 actual WASI invocations and26 Foundation reparses agree on complete
type-sensitive values and bounded summaries. Controls cover either link direction,
both directions, canonical IDs, equal IDs, no transitive closure, original payload
identity, empty/unknown/case-distinct IDs, duplicate groups/variants, child
selection, missing/disabled state and malformed excluded data. They execute a
public source-guided composition, not the shipped private previewRequests method.
Disposable source/focused/composition/WASI replay passes; full338-test output is
retained separately. wasm32-wasip1 is exercised; browser WASM is not established.

REA6.2.0 command/catalog identity matched; session closed/provider binding null.
No unchanged Ghidra/import/UI retry. The initial fixture generator sliced at an
earlier local variable and omitted the base cases; Swift compilation failed,
then the slice boundary was corrected. A metadata-result projection error and a
sandbox process inventory failure were also retained as tooling failures, not
native behavior. Exclusive controller lock held throughout. Raw Apple assembly
stays ignored/local. No native process action or global resource settlement.

Next: recover capability/mode fallback and complete request fields/variant loop,
then service/transport mapping and actual native lifecycle/rendering/resource
correlation through permitted typed routes. Both milestone contracts remain open.
