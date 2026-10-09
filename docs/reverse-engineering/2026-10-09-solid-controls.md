# Non-text Canvas controls and window lifecycle

## Discriminating rendering experiment

Prior text/VStack snapshots showed only window chrome. New preview definitions 2/3 contain explicit sRGB red/blue rectangles at 320×160 points, without text, fonts, stack layout or app-state dependencies. If the whole view path failed, their center patches would remain white; if a narrower composition path failed, simple colors could render.

Sealed run `20261009T154817Z-native-canvas-solid-view-controls-f9a90f47` returns two 640×384 PNGs. Each 32×32 center patch matches its independently predicted RGBA literal exactly: 1,024 pixels per color, 8,192 compared bytes including alpha. Images were visually inspected. This establishes the specific non-text path, not full-frame equality, text support or a recovered wire contract. The previous blank text observation remains valid for its measured inputs; these changed controls falsify a blanket claim that all view content is absent.

The independent ImageRenderer run `20261009T155055Z-native-solid-renderer-oracle-b779b982` captures red/red/blue in fresh owned processes at 320×160, scale 1, Aqua. Entire decoded RGBA frames match separately generated color-literal expectations: 614,400 bytes including alpha, no differing bits. Unchanged red PNG bytes also repeat exactly. This checks decoded pixels, not an independent PNG encoder or raw bitmap row padding. Neither renderer tier supplies Canvas transport evidence.

See [verified anchors and exact comparisons](../../research/evidence/canvas-solid-controls-2026-10-09.json), [Canvas patch fixtures](../../tools/re/fixtures/CanvasSolidOracle/manifest.json), and [separate renderer fixtures](../../tools/re/fixtures/SolidRendererOracle/manifest.json). Toolkit remains 23 adapters / 19 MCP tools; all 94 tests pass. A single changed alpha bit in the predicted patch fails its verifier.

## Corrected window lifecycle

The user identified accumulated Xcode windows and required closing each completed window before opening another. Two stale generated PreviewLab workspace windows were closed through the computer-use tool after verifying their exact owned paths. The read-only Xcode window list then reported no workspace windows. The welcome window was also closed; Xcode itself and its retained approved broker were not terminated.

Capture now checks the window list before creating/opening another workspace. A prior generated workspace or unknown listing format fails closed. Unrelated user projects do not trigger closure. `workspace-lifecycle.json` records the exact cleanup target before launch, including failed attempts. The chat agent must close that owned window through the UI at completion and verify cleanup before the next attempt; the Python worker does not pretend to provide UI automation. Regression tests cover stale-owned blocking, preservation of other projects and malformed listings.

## Next boundary

Discriminate plain Text from stack, font and frame/background composition, then establish repeatability and complete pixel expectations for the supported Canvas subset. Perform window cleanup between attempts. Actual runtime hooks, correlated XPC envelopes, reuse/completion semantics and full release observables remain open. O2/O3 and both milestones stay open.
