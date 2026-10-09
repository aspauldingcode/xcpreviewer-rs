# Matched roots and pinned color scheme

## Discrimination and result

Matched inline and custom `ProbeView` bodies use identical text, stack spacing, title, geometry and forced white background. Under inherited color scheme, all four captures are blank; inline/custom PNGs and pixels match, and a label-only change remains invisible. The sealed run is inconclusive for content acceptance. This rules out root construction alone as the observed distinction.

A dependent control pins the view environment `colorScheme` to light; its shared preview title also changes from Root control to Light root control. The title factor is not independently isolated across these runs. Both roots now show content and match exactly. The unchanged inline capture repeats PNG bytes and every decoded RGBA pixel. A label-only change affects 5,910 pixels and the separately checked interior, with identical preview titles. The light run supports all declared checks. Custom baseline was visually inspected and shows both expected labels.

Pinning light context therefore fixes this measured forced-white fixture. Default foreground/background contrast is the supported explanation; no runtime color-value dump or universal SwiftUI behavior is claimed. System appearance settings were not changed. The snapshots remain 640×384 with native window chrome, system fonts and this pinned native environment. Byte equality is native repeatability, not independent portable-renderer equivalence or raw IPC row-padding verification.

See [sealed runs, anchors and comparisons](../../research/evidence/canvas-light-root-2026-10-09.json) and [small native fixtures](../../tools/re/fixtures/CanvasLightOracle/manifest.json). Root equality and label change are separate pairs: the general first-pair `controlled_change_visible=false` does not contradict the explicitly measured label A/B.

## Verification and cleanup

A new guard test rejects a change restricted to window chrome as a label-body change. Final full suite: 95 tests pass with ResourceWarning treated as error. An initial owned process-group cleanup PermissionError was retained; isolated core tests and final full rerun pass. Both native campaigns retain frozen sources, failure results and checked artifact hashes.

Each owned workspace was closed at completion through verified UI state before the dependent project opened. Final read-only listing reports no workspace windows. Xcode, unrelated projects and retained bridge were not terminated.

## Remaining gate

The pinned light fixture now provides usable native content, exact repeat and controlled change evidence. O2/O3 remain open for required environment coverage and complete native oracle acceptance. Next isolate the appearance effect with unchanged preview titles, recover correlated transport with changed instrumentation, and compare native content against independent whole-frame expectations. Resource completion, GPU fences, final reclamation and cross-platform runtime remain separate unknowns; neither milestone is complete.
