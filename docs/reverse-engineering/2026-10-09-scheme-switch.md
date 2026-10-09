# Same-definition color scheme reversal

The prior inherited/light comparison changed preview titles across runs. This control holds preview definition index 15, title “Scheme switch”, labels, geometry and view body fixed in one owned mutable workspace. Only the marked explicit `.environment(\.colorScheme, .dark/.light)` value changes: dark → light → dark. System settings remain unchanged.

All declared checks pass. Interior ink counts are 0 → 6,286 → 0; light content was visually inspected and shows both expected labels. Dark/light differs in 6,710 full-window pixels. The two dark snapshots match all 13,866 PNG bytes and all 983,040 decoded RGBA bytes, without resize or profile conversion. The light interior also matches 589,824 RGBA bytes from the prior sealed custom light fixture exactly, excluding title and corners.

Source hashes match independently generated mutations of the fixture; only the marked value changes. The copied workspace source is restored to its original hash. The controller freezes implementation and seals artifacts; verification passes. The owned workspace was closed through UI and the retained bridge then reported no workspace windows.

The title factor is eliminated for this within-run change. Foreground/background contrast is the supported scoped explanation, not a runtime dump of SwiftUI foreground values. This is native repeatability and source-response evidence, not an independent portable pixel oracle or complete Canvas IPC capture. Fonts, scale, appearance coverage, raw transport padding, completion and final reclamation remain open. O2/O3 and both milestones remain open.

Evidence: [sanitized results and anchor](../../research/evidence/canvas-scheme-switch-2026-10-09.json), [owned snapshots](../../tools/re/fixtures/CanvasSchemeOracle/manifest.json). Run `20261009T162104Z-native-canvas-same-definition-scheme-6556218b`; manifest SHA-256 `e92880dd2d05565797e9e232f441c1851eeafad8eb24dbbae5ff736887c5e1df`.
