# Multi-selection state calculation and child-row replacement

Recovered complete PreviewsXcode updateChildConfigurations method, animation body,
closure thunk and multiSelection write closure: 2,652 bytes matched against actual
Mach-O bytes and independent LLVM disassembly. Metadata names the five row-entry
fields; exact imported getters/setters/withAnimation/empty storage/defaultSelection
bindings are asserted. The method snapshots direct variants selected by requested
IDs in source order. The animation body clears child rows unconditionally, appends
the matching immediate child configurations for each selected root occurrence,
and unions those children's recursive defaults. Duplicate roots repeat rows.
The setter unions requested IDs with returned defaults and compares canonical Set
membership before replacing selection. Enablement is preserved. Equal selection
membership preserves stored representatives but does not bypass child-row rebuild.
Own defaults, orphan child entries and child-added IDs do not activate root rows.
Unknown requested IDs survive. No requirement that defaults belong to variants.

The original Rust API mutates owned VariantGroupSettings only when membership
changes and returns the complete replacement child-row array by borrowed reference.
It neither reproduces intermediate binding write notifications nor runs animation.
The original bounded inspector exposes the calculation with required configuration,
Bool isEnabled, selection and requestedSelection String arrays. Its derived report
is not an Apple wire type. The complete configuration is validated before use,
including malformed unselected children. Summaries cap eight IDs/four child titles
at escaped 256-scalar previews. Existing wire codecs remain unchanged.

323 Rust tests; 26 original public Swift/Foundation compositions (20 accept/six
reject); 46 actual WASI invocations (26 canonical +20 summaries),20 Foundation
reparses and byte-identical summaries pass. Three new tests compare complete values,
repeated updates/equal membership, child-row replacement and bounded CLI output.
Source and focused/public-composition/WASI replay runs in a disposable directory.
Expected decode rejections are controls, not native setter failures.

These are original compositions using public Swift Set/Dictionary and Foundation
serialization, not invocations of the shipped private SwiftUI setter or defaults
getter. Portable deterministic recursive-default order inherits the documented
native sibling representative discrepancy. Other inherited canonical-key collision,
Unicode16, depth and codec error-order limits remain. Native SwiftUI bindings,
animation, persistence, single-selection and UI actions remain unverified. No
Xcode/simulator process action or provider/global resource settlement is claimed.

REA 6.2.0 command/start/package/catalog identity matches the prior pinned identity;
server session closed and provider binding null. Initial binary_session call with
unsupported action key failed validation; corrected empty-argument read succeeded.
The server's alignment field stays unknown without expected identity arguments;
the recorded fields were compared explicitly. Ghidra/missing MessagingHost module
limitations remain scoped to their prior probes. No new plugin import attempted.
Raw Apple assembly and full symbol inventories remain in ignored local research/raw.
Both milestones remain incomplete. Next: singleSelection write/read, isOn, caller
wiring and Pipeline previewRequests/content-override construction, with actual
native lifecycle/transport/rendering/resource observations still required.
