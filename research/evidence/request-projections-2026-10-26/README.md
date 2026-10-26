# Admitted request display/override/variant projections

Recovered the post-admission portion of Pipeline EditorSettings.previewRequests
and PreviewDisplayMode value witnesses.5,748 selected bytes independently match
LLVM/Mach-O. Actual PreviewCapabilities field vector indices4/5 identify continuous
live preview and static preview support. PreviewRequest.configuration refers to
PreviewRunnable.Configuration (displayMode,overrides,controlState), not the separate
PreviewConfiguration/ExecutionPointProperties updateMode. Named enum descriptors,
case globals and witnesses qualify interactive Bool payload bytes0/1 and static2.
CanvasMode is live(HostLocation),grid(Group),static; HostLocation inCanvas0/external1.
The exploratory attempt to resolve a local symbolic target as an import failed;
local descriptor567218 identified PreviewRunnable.Configuration instead. No guessed
private ABI execution occurred. A guessed append callsite6fb74 was an ADD; actual
BL6fb7c and exact target were checked after bounded disassembly.

After earlier admission succeeds, live always adds one variant-less interactive
request; other modes do so only with continuous live support. The interactive Bool
payload is false for live(external),true otherwise. Its broader runtime/UI meaning
is not inferred here. These requests carry all effective overrides, excluding the
grid ID when applicable. They do not apply associated-group filtering.

Without static support, return the current array. With static support, append a
variant-less static request when mode is static OR the current array is empty.
Its overrides are the same all-effective array. Thus static mode may produce both
interactive and static requests, and grid without continuous support gets a
variant-less static request even with empty/missing grid sections. Live already
has an interactive request, so does not add this static base request.

Grid then appends one static request for every variant in every section, preserving
section/element order and duplicates. Each uses the supplied grid payload and the
previously recovered direct association-filtered override array. No discovered
lookup replaces the payload; no deduplication. Empty/missing variants configuration
adds none. Each present variant is copied; input state is unchanged. No per-variant
interactive request is created by this loop.

Original request_projection::admitted_request_projections and request-projections
inspector implement these displayMode/overrides/optional variant projections.
Input mode is already resolved by the caller; earlier app/provider admission,
instance/destination/origin, control state, localization, context/identity and
full native request fields remain outside this contract. The projection schema
is original tooling, not Apple wire serialization or a complete PreviewRequest.
The native method is not invoked and execution/rendering/lifecycle/resource parity
is not established. Existing Unicode16 and codec boundaries are inherited.

341 Rust tests pass, including three new complete-value/input preservation/owned
output/CLI summary/rejection checks.36 original public Swift/Foundation compositions
(28 accepts/eight rejects),64 actual WASI invocations and28 Foundation reparses
agree on complete type-sensitive values and bounded summaries. All four modes
(live inCanvas/live external/static/grid) across both capability Bools are covered,
plus empty/missing grid configuration, disabled/missing state, one-level child
selection, both association directions, canonical IDs, duplicate groups/variants,
original payload identity, inactive payload fields, malformed active/excluded data,
strict Bool rejection and long/many bounded summaries. Controls are source-guided
public compositions, not native private-method output. Disposable source/focused/
composition/WASI replay passes; full341-test output retained separately.

REA6.2.0 command/catalog identity matched; session closed/provider binding null.
Exclusive controller lock held. Raw Apple assembly remains ignored/local. No
unchanged UI/Ghidra/import failure loop or native process action/system change.
Browser WASM, native request scheduling, transport and global resource settlement
remain unverified. Next: recover admission and omitted full request fields/service
mapping; correlate actual permitted native lifecycle/rendering/refresh/resources.
Both milestone contracts remain incomplete.
