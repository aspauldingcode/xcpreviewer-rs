# Single-selection cleanup and child-row replacement

Recovered complete PreviewsXcode singleSelection write closure1ee884..1ef1b8:
2,356 new bytes,5,008 including inherited complete child-update/animation-body,
thunk and multi-select setter ranges. Every instruction matches independent LLVM
output against the pinned Mach-O. Exact imported current selection, direct variants,
child dictionary, immediate child variants, ID, selection setter and Binding setter
calls are asserted. Direct Set remove/insert, singleton construction, child-update,
formUnion, equality and conditional write callsites are checked.

The single-selection setter starts with current stored selection. For every root
whose ID differs canonically from the requested ID, it removes that root ID and
its immediate child variant IDs. This cleanup happens even if the root was not
selected. It preserves unrelated IDs, grandchildren, orphan children and existing
values under the chosen root. Then it inserts the requested opaque ID (empty and
unknown allowed), rebuilds child rows from matching direct variants using a chosen
singleton, and unions recursive defaults from those children. It preserves
enablement. Equal membership skips the state write, preserving stored spellings,
while still rebuilding child rows. Duplicate chosen roots repeat child rows.
Child-added IDs do not activate additional root rows.

Original Rust update_single_selection and a canonical VariantIdSet::remove operation
implement this calculation. The bounded update-single-selection inspector takes
required configuration, strict Bool isEnabled, selection String array and
requestedVariant String. Its complete derived report is original, not Apple wire
serialization. All configuration/ID validation precedes calculation, including
unselected malformed children. Shared multi-selection inspector remains covered by
full tests. No intermediate native Binding notifications, animation, persistence
or actual production caller wiring is implemented or claimed.

326 Rust tests,26 original public Swift/Foundation compositions (20 accepts/six
rejects),46 actual WASI invocations (26 canonical+20 summaries),20 Foundation
reparses pass. Complete values match type-sensitively; summaries match bytes and
remain bounded. Three new tests cover complete calculations, repeated updates,
canonical removal and CLI reports. Disposable focused/source/composition/WASI
replay passes; full test output retained separately. Public native compositions
use original Swift Set/Dictionary/Foundation code, not shipped private methods.

Recursive-default deterministic traversal/native sibling representative discrepancy,
Unicode16, canonical child-key collision restriction, depth and codec error-order
limits remain inherited. Neither private setter/getter nor native animation/UI
binding was invoked. Both milestones remain incomplete. REA identity matches the
prior pinned tuple; session closed/provider binding null; server alignment field
unknown without expected identity input, explicitly compared recorded fields.
No new Ghidra/import failure probe, Xcode MCP, native process action or resource
settlement claim. Raw Apple assembly stays in ignored local research/raw.

Next: singleSelection read closure/property availability, isOn, actual transition
caller wiring and Pipeline previewRequests/content-override construction. Native
transport/lifecycle/refresh/rendering/provider/global resource parity stays open.
