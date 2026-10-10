# Public native primary-layer extent holdouts

The predeclared source-over model matches all 80 public native callback allocations
at the newly tested dimensions. This extends the native reference denominator
beyond the previous fixed 17×9 target. It does not recover Canvas transport or
establish native getter/PNG equivalence.

Four alpha cases (4, 8, 18, 19), both layer orders, two repeats, and five target
layouts were frozen before execution: 1×1 at strides 4/16, 13×7 at strides 52/64,
and 64×64 at stride 256. The owned Swift fixture uses explicit sRGB primaries,
ImageRenderer scale 1, no drawing group, and an sRGB RGBA premultiplied-last
callback context. Reported size, callback count, actual context dimensions/stride,
format and color space are checked separately.

Each 16,384-byte target starts with zero active pixels, A5 row padding and C3
unused tail. Independent Fraction predictions include every target byte. All
1,310,720 compared bytes match: 273,920 active pixel bytes, 1,536 row padding
bytes and 1,035,264 tail bytes. All 40 A/A full-allocation repeat pairs match.
Predictions use the previously declared quantized-stage model; this is a finite
extent holdout, not evidence that arbitrary SwiftUI views share that model.

The completed run is `20261010T215252Z-native-primary-extent-holdouts-5143e5b4`,
manifest SHA-256 `5786fc404ec0181161d42e431b303425260af6adb3d517bf92351cbf542301fa`.
The separately retained hash and all sealed artifacts verify after completion.
Full predictions, captures, metadata and byte comparison diagnostics remain local.
The sanitized [receipt](../../research/evidence/native-primary-extent-2026-10-10.json)
contains the public conclusions and anchors.

Two artifact-limit failures are retained: `20261010T215034Z-native-primary-extent-holdouts-a7595765`
and `20261010T215216Z-native-primary-extent-holdouts-2ebcd1d7`. Both seals verify;
neither supplies pixel acceptance. The first experiment used an insufficient
32 MB Swift module-cache cap. The second graph run retained that same 32 MB shared
cap despite the corrected per-experiment cap. Final execution used 256 MB at both
levels and the unchanged 180-second subprocess/controller deadline. Resource-busy
attempts executed no experiment and did not interrupt the other controller.

Graph selection and planner inspection identified this independent oracle while
unrelated source-frame implementation was being edited. The bounded graph run's
budget failure was retained; its failure fingerprint does not include graph
budget configuration, so the changed shared-cap retry used the existing serial
controller entry point and exclusive lock. No failure ledger was cleared or
active graph wake rewritten. The corrected separate extent runner configuration
is retained. This limitation should be addressed when reviewing the concurrently
developed graph runner.

Two extent-specific tests pass, covering full padding/tail predictions and typed,
exclusive adapter selection. The working-tree repository suite passed 337 tests
in 25.609 seconds; that snapshot also included unrelated graph/source-frame tests.
The exact isolated staged implementation separately passed 317 tests in 29.944
seconds, excluding all concurrent graph/source-frame changes. Fresh-process
verification independently recomputed the successful frozen checks.
No Xcode windows or browser tabs were opened. No user processes were terminated.
Both delivery milestones remain open.

Next: use this sealed native extent reference in the supported source-to-frame
CLI corpus, including transparent PNG conversion controls. Raw callback target
bytes and explicitly converted PNG pixels must retain distinct claim scopes.
