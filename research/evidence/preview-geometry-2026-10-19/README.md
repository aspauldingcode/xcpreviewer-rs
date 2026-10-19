# Selectable-region and preview point-space reconstruction

Direct shipped-code analysis now connects region geometry in PreviewsMessagingHost to the PreviewGeometry coordinate getters in PreviewsPipeline. REA6.2.0 server/target identity was confirmed; GhidraVibe imported the current ARM64 pipeline and decompiled selected functions. Raw pseudocode/disassembly remains local and its hashes are retained. Both framework hashes match prior pinned identities. The prior bitmap-image evidence seal was fully reverified. Acquisition used the exclusive controller lock, bounded native subprocesses and15-second focused decompiler deadlines. The REA session and analysis lock were released. No Xcode MCP/bridge, private Swift ABI call, Frida retry, user UI or workspace operation was used.

## Recovered source contract

- MessagingHost SelectableRegion.scaledBy at0x4b828 (228 bytes) checks CGRectIsNull and CGRectIsInfinite. Those rectangles pass through unchanged. Otherwise it multiplies the original x/y by the factor and multiplies CGRectGetWidth/GetHeight by the factor. The latter use absolute extents. This does not standardize/shift the origin as an affine rectangle transform would. Path and optional accessibility Data are copied unchanged.
- Pipeline PreviewGeometry.selectableRegionsInPointSpace at0x32366c (448 bytes) maps the ordered regions with factor1/scaleFactor. The addressable wrapper at0x257100 (132 bytes) retains its ModelPath field while scaling the base region. The reconstruction does not implement ModelPath parsing or the wrapper's complete model semantics.
- Pipeline PreviewGeometry.sizeInPoints at0x323624 (20 bytes) divides each stored raw pixel dimension directly by scaleFactor. ARM64 has two direct fdiv instructions. The region getter separately computes a reciprocal and calls scaling. These produce observably different rounding for width7/scale3; sharing one arithmetic shortcut would be incorrect. No scale-zero or nonfinite guard is present in these recovered paths.

Focused imported-function xrefs were incomplete; symbol-directed recovery identified these consumers. This does not establish a complete lifecycle call graph or imply that input dispatch is absent.

## Independent native boundary and verification

The original C oracle uses public CGRect classification/accessor functions and the exact recovered arithmetic sequence, without invoking private Swift code. It freezes180 cases:18 rectangle shapes/sentinels times10 scale values. Cases include positive/negative extents, negative zero, null/infinite sentinels, mixed infinite origins, NaN, sentinel near-neighbors, negative/zero/infinite/NaN factors, fractional scale and direct-division rounding differences. This is a public-primitive oracle for the recovered algorithm, not an observed private Canvas call.

Every non-NaN result is compared by its64-bit representation, including signed zero and unchanged sentinel fields. NaN results are compared by classification; NaN payload/sign and floating exception flags are not claimed equivalent. The measured64-bit CGRectNull guard recognizes positive infinity in either origin component. CGRectInfinite is a finite four-component sentinel; IEEE infinite extents alone do not qualify. The portable implementation uses the measured sentinel and guard; coverage is the pinned64-bit source/public-oracle corpus, not universal CoreGraphics classification on every architecture/input.

The original Rust module adds Rect.scaled_by, SelectableRegion.scaled_by, regions_in_point_space and size_in_points. It preserves region order, path, accessibility bytes and original inputs. It intentionally preserves recovered IEEE behavior rather than introducing UI validation. Thirty Rust tests pass:26 prior plus4 geometry integration suites, including180 native cases and a binary-payload-to-point-space check. An independent replay rebuilds the public oracle, reproduces the complete frozen JSON and generated Rust fixture, runs the Rust tests and checks the CLI without modifying source. replay.log records that replay.

## Usable inspection

```sh
cargo run --offline -p canvas-core --bin inspect-preview-geometry -- tools/re/rust/canvas-core/tests/fixtures/payload-defaults.bplist
```

The CLI displays bitmap pixel dimensions, scale and point dimensions, then each region's pixel/point rectangles and metadata size. For the owned fixture, scale3 maps x=-1.5 to-0.5 and y=2 to0.6666666666666666; bitmap3x2 yields point size1x0.6666666666666666. Taking bitmap dimensions as inspection input is this adapter's explicit choice; other native preview geometry may be supplied independently. This command does not send input, perform hit testing or provide a GUI canvas.

## Next native/protocol frontier

Trace RemoteEventPayload's codec and stream, then its runtime/input consumer. Current matching symbols identify RemoteEventPayload.init(propertyListValue:) at0xafd2c, its serializer at0xaf9c0 and the previewRemoteEvents stream getter at0xae744 in the pinned MessagingHost. CanvasControlEvent is a separate control path and must not be conflated with view input. Recover discriminants/payloads and correlate a changed permitted runtime observation before claiming interaction. Refresh/state, native R1/R2 resource accounting and both milestones remain open. No private Canvas transport or live input acceptance is inferred from these geometry results.
