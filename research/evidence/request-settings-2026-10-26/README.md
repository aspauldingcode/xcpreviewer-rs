# Preview settings admission and opaque control-state propagation

Recovered268 selected bytes for request admission and PreviewSettings default
construction; complete selected instructions match LLVM/Mach-O. The native method
gets PreviewInstance.id, wraps DiscoveredItem.ID.preview, and looks up field6
EditorSettings.discoveredItemSettings. Empty dictionary or missing entry chooses
field7 defaultPreviewSettings. A found row supplies its isEnabled byte and state
array as a whole. Disabled returns the empty request array; enabled continues.
Native PreviewSettings.init initializes disabled with an empty array. Named
metadata, ID getter and constructor symbols, descriptor links, branch instructions
and selected array storage are pinned. The key is structured, not a plain String.

PreviewSettings.boxedCanvasControlStates and CanvasControlState.states share the
same Array<HashableBox<PlistValueBox>> typeref. The selected array is retained and
used in variant-less interactive/static and per-grid-variant configurations. These
three stores are pinned in the predecessor builder range; no merge, filtering or
deduplication appears in this propagation. Native boxed value encoding, contents,
identity/equality/hash/lifetimes and transport semantics remain unverified.

Original PreviewSettings<T>,ConfiguredRequestProjection<T> and generic
configured_request_projections accept the caller's optional stored row plus
required defaults. Native key construction/lookup is caller-owned. A present row
wins even disabled or empty; missing uses defaults. Disabled returns no requests;
enabled uses admitted projections and clones the selected ordered state array
into every result. T is an opaque host-owned value/handle. No state installation,
persistence, box interpretation or resource settlement modeled. Default<T> is
disabled/empty without requiring T:Default.

configured-request-projections inspector adds original settings dictionaries to
request-projections inputs. Opaque control arrays use arbitrary supported plist
values to demonstrate propagation, not native box codec equivalence. Canonical
reports include controlState array in each request. Summary exposes counts only.
All active inputs and both rows validate first, even disabled/unused defaults;
this is an explicit tool schema/domain policy, not native settings decoder parity.
Existing admitted/grid commands retain their output contracts.

344 Rust tests pass, including three new complete-value/input preservation/owned
control-array/CLI checks and constructor-default assertions.45 original public
Swift/Foundation compositions (34 accepts/11 rejects),79 actual WASI runs and34
Foundation reparses agree on complete type-sensitive values and bounded summaries.
Stored/default enabled combinations, stored-empty precedence, duplicate/mixed
opaque states, unchanged mode/capability matrix and grid filtering, strict Bool
and invalid unused/default/disabled values are covered. Controls are original
public compositions, not native private-method/box output. Disposable source/
focused/composition/WASI replay passes; full344-test output retained separately.

Two implementation/tooling failures were corrected: fixture prefix slicing hit an
earlier local variable and produced invalid Swift; final-occurrence boundary fixed
it. CLI summary attempted Display on OsString; explicit known command label fixed
it. Initial Rust compiler output retained. REA command/catalog identity matched,
session closed/provider null. Controller lock held. Raw Apple code remains local.
No native process action/system change; both milestone contracts remain incomplete.

Next: recover structured discovered-item/preview identity and native box/control
state codecs where useful, remaining full request fields/localization/context,
service mapping and actual lifecycle/rendering/transport/resource correlation.
