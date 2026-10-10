# Same-instance mixed-alpha renderer order

The fourteen owned Color inputs,17×9 output,scale1,nonlinear sRGB and Aqua appearance are held fixed. Competing explanations were declared before acquisition: a retained provider could change after later renderer operations, getter/cache initialization could depend on call order, or getter and drawing paths could have distinct quantization.

The fixture forces a new owned `Data(bytes:count:)` copy immediately after each cgImage getter. It retains the first CFData provider separately and copies it again at every stage. Snapshots bracket two public rendering callbacks and nsImage/TIFF/PNG export. Two independent call orders start with cgImage or the public drawing callback. Each case/order repeats in two fresh processes. Every callback must execute exactly once and report17×9; its independently initializedRGBA8 target has stride80, zero active pixels and12 sentinel padding bytes per row. Metadata, full extents and source expectations are checked explicitly.

Same-instance public renderer order:56 fresh processes,224 immediate provider copies plus224 retained snapshots (274,176 bytes),112 callbacks (80,640 complete bytes including12,096 padding). All168 repeat pairs and168 call-order pairs equal. Getters and retained provider bytes stable across both callbacks and nsImage export; case12 remains blue8 getter versus7 callback in all8 targets. Reused56 exports/34,272 decoded bytes satisfy224 measured-provider relations,28 repeat pairs and28 order pairs. No general color formula or native Canvas wire claim.

All224 getter snapshots also equal the externally anchored prior native provider measurements. Every getter and deferred original provider stays byte-identical within the captured sequence. Case12 produces `(1,4,8,96)` in immediate getter copies and `(1,4,7,96)` in callback targets. Every153-pixel target has the blue discrepancy; all padding staysa5. The call-order/shared-provider hypotheses have no supporting observation under these controls. The remaining difference is scoped to the public drawing versus getter paths, without identifying an internal algorithm.

Five predeclared rational/float source models are retained separately in comparisons; only the opaque source control is required to pass. Equality to a measured native getter is a relational check, not an independent reconstruction of mixed-color quantization. No pixels or color channels are normalized to make them match.

The dependent comparison-only experiment verifies the original acquisition seal before decoding all56 exported PNGs. Integer half-up unpremultiplication of each immediate provider predicts the complete612-byte RGBA export. All224 stage/export relations,28 repeat pairs and28 order pairs pass. These are reused captures, not56 additional acquisitions. PNG decoding is explicit; container-byte identity is not claimed.

Sealed acquisition: `20261010T182739Z-native-mixed-alpha-render-order-9d110f33`, manifestSHA256 `195b54b87dc547bcc0a5d187f0b454f53ab946f7dce0813ee6bfab2b0765f236`.

Sealed dependent export comparison: `20261010T182852Z-native-mixed-alpha-order-export-contrast-8b6e0df7`, manifestSHA256 `0a83c346c22bd8fb0182bccba666dfdefd652c5105831cdd4976ba1242715d36`.

Environment: macOS26.5.1 build25F80,ARM64,Apple Swift6.3.3. No Xcode workspace opened; no private process attachment or system protection changes. 287 tests pass. Full suite and byte-corruption controls validate metadata, mode separation, missing anchors and unmatched tails. Next discriminator: rasterization scale with fixed output extent and source input. Both milestone contracts remain unfulfilled; these public owned measurements do not establish native Canvas IPC or universal SwiftUI compatibility.
