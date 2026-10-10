# Actual Linux primary-layer verification

The pinned import-free renderer/checker from the portable primary-layer experiment executes on an existing LinuxARM64 host with Wasmtime49.0.0. This extends runtime verification to an actual Linux kernel, not just another macOS interpreter. The source remains compiled on macOS and the Linux VM runs on Apple hardware. The declared output is a primary-only premultiplied callback-target allocation; native cgImage/PNG differs and is not claimed equivalent.

Actual Linux ARM64 Wasmtime49 primary-layer execution:320 complete allocations/5,242,880 independent bytes plus same extent cross-host equality;80 full native-prefix comparisons/57,600 reused native target bytes;17 invalid requests/278,528 unchanged bytes.200 native checker controls including160 channel/alpha/padding/tail faults. Both semantic mutants rejected;all80 per-case counts match anchored V8. Owned containers removed,two existing containers preserved. Getter/PNG differences remain;no Canvas/SwiftUI equivalence.

The standalone runner instantiates320 fresh renderer instances at four dimensions/strides, two layer orders and two repeats of20 alpha triples. Every16,384-byte allocation is compared to independently calculated sealed Fraction expectations and the corresponding V8 buffer. Padding and unused tail remain byte-visible; no channel/alpha normalization occurs. The80 native-compatible geometry comparisons retain the original720-byte padded native target prefix and separately declared tail. They compare1,310,720 complete bytes, containing57,600 reused native bytes, not additional native acquisitions.

All17 unsupported requests return0 and retain the complete previous allocation. The frozen-native checker executes40 targets×5 modes individually; every baseline returns0 differences and every channel/alpha/padding/tail fault returns exactly1. Interpreter stores enforce131,072-byte memory bounds and10,000,000 fuel per call. Host/frame/module/control identity metadata is validated, including strict integer types; rehashed corrupted payloads still fail independent exact-byte comparison.

The dependent experiment executes the exact two previously sealed algorithm mutant modules on Linux. It compares all80 per-case mismatch counts to V8, verifies aggregate rejection, and retains both case4-forward witnesses of306 differing bytes. Source-alpha truncation still changes17 targets;forward layer reordering changes16. Endpoint controls remain equal. These checker calls inspect full buffers internally; no additional raw mutant frame acquisition is claimed. Aggregate fuel is bounded at50,000,000.

Docker uses the existing pinned local image with `--pull never`, network disabled, read-only filesystem, all capabilities dropped, no-new-privileges,64 PID limit,256MiB memory,one CPU and the current user's UID/GID. The native evidence and verified extracted Wasmtime wheel are read-only mounts. Each invocation has an independent nonce/name/owner label. Cleanup verifies that label before removing only its own container. Both owned containers are absent afterward; the two preexisting containers remain exactly unchanged. No VM lifecycle changes,image pulls or system protection changes occur.

Observed kernel:`6.8.0-100-generic`;architecture:`aarch64`;runtime:`Wasmtime49.0.0`. Runtime wheel contents are byte-verified against the pinned wheel, not merely identified by the wheel filename. Container image and wheel identities are retained in sanitized evidence.

First seal:`20261010T190443Z-linux-primary-layer-control-86feb1b8`, SHA256 `21c73bdc7cc0c687e26ca2ebf539dce61b6a3303779b4e5f5857e9aced2c2934`.

Dependent semantic-mutant seal:`20261010T190617Z-linux-primary-layer-algorithm-mutants-76b47f3c`, SHA256 `8494f511cf0d9b0c0b6be90f7121b1ee44a3d34793102dd642b235a8ad762ae6`.

Next:strict primary-layer source-to-IR parsing and diagnostics under this explicit supported output contract. Linux compiler/frontend execution, browser,Windows,independent non-Apple hardware,performance and both milestone acceptance contracts remain open. No native Canvas transport or general SwiftUI reconstruction follows from these owned controls.

301 tests pass,including strict host/module/bounds/control metadata and rehashed pixel/alpha/padding/tail corruption,invalid buffers,semantic-mutant identity and mode separation.
