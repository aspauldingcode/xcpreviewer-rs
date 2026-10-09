# Delayed resource reuse and independent native renderer oracle

Two sealed campaigns advance independent boundaries: eight owned cross-process surface cases (four shapes × reused/separate storage), each repeated twice, and three fresh-process SwiftUI ImageRenderer captures (A/A unchanged, A/B changed text). See [checks and manifest anchors](../../research/evidence/surface-reuse-renderer-2026-10-09.json), [surface goldens](../../tools/re/fixtures/SurfaceReuseOracle/manifest.json) and [renderer goldens](../../tools/re/fixtures/RendererOracle/manifest.json).

## Delayed consumer countermodel

The owned parent sends generation-one surface access, waits for audit-verified import acknowledgement, then prepares generation two before the child reads the first handle. The child imports generation two, snapshots both handles, releases both received Mach rights, and snapshots the remaining first CF alias again. Both directions verify kernel audit PIDs. Actual child exit, metadata, geometry, padded bytes and cleanup controls are required.

| Storage mode | Native surface IDs | Delayed first-handle pixels | Second-handle pixels | Imported first-name send references |
| --- | --- | --- | --- | --- |
| Reused surface | Equal | New seed / generation two | New seed / generation two | 2 after both imports; 1 after first release |
| Separate surfaces | Different | Original seed / generation one | New seed / generation two | Each name has 1 reference |

Repeated imports of the same Mach port coalesce its local name while retaining two user references. Releasing one does not release the other. CF aliases retain their exact pixels after both received rights are dropped. All five snapshot stages match independent expectations, including padding and the seed-255-to-zero change. The separate 3×2 delayed snapshot matches the prior native initial golden with zero differing bits, confirmed by system cmp.

This demonstrates mutable storage behavior, not Canvas's actual pool or protocol. The fixture assigns generations 1 and 2 and Mach message IDs 201 and 202; these are not recovered Apple fields. A resource ID alone cannot identify immutable frame content. A portable design needs separately defined generation/completion rules and storage protection for delayed consumers; the exact native rules still need observation. No GPU fence, arbitrary race, stale-name security guarantee or final memory reclamation is established.

## Native rendering reference tier

An owned SwiftUI ImageRenderer fixture now pins 320×160 logical/pixel dimensions, scale 1 and Aqua appearance. Two separate invocations of the same compiled executable and view variant produce identical PNG bytes and decoded RGBA pixels. A third invocation changes only the first text label, producing 1,824 changed pixels. Both images were visually inspected and contain the intended text.

The reference uses the native system title font; its exact rendering remains tied to the pinned native environment and source hash. Exported PNGs contain no embedded ICC profile. These captures support this bounded ImageRenderer reference tier; they do not establish generic color/font portability or Xcode Canvas rendering. The controlled runtime view variant is not a source-rebuild or hot-reload measurement.

![Owned native baseline](../../tools/re/fixtures/RendererOracle/baseline.png)

![Owned native text variant](../../tools/re/fixtures/RendererOracle/changed.png)

This oracle can support explicit F1/F2 subset work while Canvas discovery/attach remains blocked. It must remain separately labeled in comparisons and cannot close the live Canvas capture or wire gates.

## Verification and next work

The controller freezes source, seals artifacts, indexes scoped claims and records trusted manifest anchors. The surface verifier rejects changed padding, missing stages, wrong ID/name relationships, wrong right counts, reordered fixture generations, unverified peers and nonzero helper exits. All 83 tests pass in a context permitted to signal their own timeout subprocess group. An earlier default-sandbox test run failed that cleanup operation with PermissionError; this diagnostic is preserved separately rather than relabeled a code fix.

R2 remains open for native completion acknowledgement, stale-generation handling, cancellation and selected concurrent release behavior. O3 has a repeatable separate renderer tier; actual Canvas pixels and complete correlated IPC remain missing. R1 final reclamation, GPU synchronization, multi-plane formats and portable SwiftUI execution remain unverified. Next work should pursue a changed Canvas observation method and choose an explicit portable subset against this oracle, rather than grow synthetic generations into presumed Apple wire semantics.
