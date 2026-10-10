# Rasterization scale and drawingGroup controls

The preceding same-instance probe eliminated observed retained-provider mutation and call-order dependence for the fourteen owned mixed-alpha Color inputs. The remaining case12 difference is getter `(1,4,8,96)` versus drawing callback `(1,4,7,96)`. This experiment asks whether the public rasterizationScale parameter changes that boundary at fixed17×9 source and output geometry.

The fixture declares scales1,2,0.5,4 before execution and repeats them in forward/reverse orders. Each case/order runs twice in independent owned processes. Renderer scale1,nonlinear color,sRGB targetRGBA8,stride80 and Aqua appearance remain fixed. Every target is independently initialized with zero active pixels and12 a5 padding bytes per row. Strict metadata checks require exactly one callback,17×9 reported size, the declared scale/index/order, expected pixel format and exact720-byte allocation. Every target is compared without normalization to separately anchored native getter/callback measurements and five independent rational/float source models.

Public renderer scale and drawingGroup controls:112 fresh processes,448 exact-count callbacks/allocations,322,560 full bytes including48,384 unchanged padding bytes. Scales1/2/0.5/4 in both orders preserve prior callback pixels:448/448; getter relation416/448,onlycase12 differs. All224 repeat and224 order pairs pass. Explicit drawingGroup modifier produces equal bytes but does not prove an offscreen pass was executed. General mixed-color formula and native Canvas protocol remain open.

Each campaign has56 fresh processes,224 allocations and161,280 bytes (24,192 padding),112 repeat pairs and112 equal-scale forward/reverse pairs. In each, all224 targets equal the prior callback measurement;208 equal the pinned getter. Every scale/order has the case12 discrepancy; all153 blue bytes per target differ. The two campaigns therefore contain32 such target mismatches. Model matches per scale are36/56 for rational-half-up/f32-half-up variants and40/56 for rational-even/f32-even; no model fits the complete corpus. Sixteen opaque independent source controls pass per campaign.

The dependent probe adds exactly the public `.drawingGroup(opaque:false,colorMode:.nonLinear)` modifier to the same source and repeats the scale/order matrix. Its output is byte-identical to the prior ungrouped callback at every target. This tests visible output for this simple solid-fill source; the framework may optimize it. Modifier presence in compiled source does not prove an offscreen pass, GPU work, allocation, vector path or rendering backend. No inference about those internals is accepted.

The source model predictions, native-derived relations, complete allocations and padding remain separately reported. Both seals verify against external manifest anchors. No Xcode windows opened and no Apple binaries/private dumps published.

Acquisition1: `20261010T183453Z-native-mixed-alpha-rasterization-scale-c9636cdf`, SHA256 `e7e59c73057eb4801a306c0e0fb3afe79422b8876fe1e6adeaaf0e7156d65dcd`.

Acquisition2: `20261010T183552Z-native-mixed-alpha-drawing-group-fea18d4f`, SHA256 `80f02e84ec2de13eb02a7ea02534b0150840a08e57032c1e37c50df44120eec9`.

Environment: macOS26.5.1 build25F80,ARM64,Apple Swift6.3.3. 290 tests pass. Verification includes invalid boolean/numeric scale and target identities, changed geometry/callback accounting, invalid mode combinations and missing/mismatched anchors. The existing full-allocation pixel/padding/tail corruption controls remain active.

Next discriminator: independently predicted primary-color multi-layer source-over views with modifier/no-modifier and scale controls. This adds an actual composition workload without assuming framework internals. General mixed-color reconstruction, native Canvas transport, and both milestone acceptance contracts remain open.
