# Literal view expression to LLVM/WASM feasibility

This experiment implements a deliberately bounded expression frontend, not a Swift compiler or general SwiftUI runtime. It advances F1/F2 without depending on the unchanged native Canvas instrumentation or REA full-image import blockers. No Xcode windows, new dependencies or services were required.

## Supported source contract

The exact supported shape is an ASCII expression fragment:

```swift
Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1).frame(width: 320, height: 160)
```

Red/blue accept only the pairs `(1,0)` and `(0,1)`. Green is zero and opacity is one. Width and height are integer literals in ranges 1..320 and 1..160, respectively. ASCII whitespace may vary; source length is bounded to 4,096 characters. The color constructor and argument order are fixed. Named colors, imports, declarations, state, text, modifiers, other color spaces, fractional colors/dimensions, expressions, comments and trailing input are unsupported and reject. This is a custom frontend for an explicit syntax subset; a complete Swift source program is not accepted.

Explicit sRGB constructor values match the actual frozen native reference construction in `SolidReference.swift`. Named `Color.red`/`Color.blue` spellings were used in the initial candidate but removed from the accepted contract: matching their system-dependent semantics against the explicit sRGB oracle had not been established.

## Executed portable boundary

Each accepted fragment produces a checked literal configuration, then a generated C kernel, saved LLVM IR, and a WASM module linked from that saved IR. The generated C is revalidated before interpolation. A fixed 204,800-byte buffer supplies bounded opaque RGBA pixels. The exported renderer accepts a row stride in the range `width*4..1280`; each padding byte is explicitly `0xcd`. Invalid stride returns zero and preserves the complete buffer.

The module exposes `render`, `pixels`, `capacity` and memory. Node V8 instantiates with zero WASM imports; no Apple native runtime or render fallback participates in module execution. Clang, linker, Node/V8, source, IR and module identities are retained in sealed artifacts. Clang/linker/host calls have 30-second subprocess deadlines within the 120-second controller deadline and exclusive controller execution.

Native references are separately anchored to owned ImageRenderer run `20261009T155055Z-native-solid-renderer-oracle-b779b982` and manifest SHA-256 `2fbbdb58072cd32f287fdd841eb072cd8f925513e4fd2c4323bf38fe11b8cf3c`. This oracle is not a Canvas transport capture. The source fragments themselves were not independently compiled by Swift in this experiment; native comparison uses the prior equivalent explicit color/frame construction.

## Exactness and failures

Four builds execute red, identical red, blue and a 3x2 padded red fixture. Full RGBA output compares with 614,400 decoded native bytes for the three 320x160 frames. Independent literal expectations compare all 614,432 bytes across all four outputs, including the eight row-padding bytes in the small fixture. Repeat pixels, normalized IR and complete WASM module bytes are equal. Fifteen unsupported-source holdouts reject. Sixteen invalid-stride calls each preserve all 204,800 buffer bytes.

Four sealed runs retain the investigation. The first two produced exact pixels but different repeat WASM bytes, so acceptance remained inconclusive. LLVM header source paths differed; normalizing only the first two file-metadata lines made IR reproducible but did not resolve module inequality. A separately observed one-byte difference was the output filename in the optional WASM custom name section. Link-time stripping removes optional names; it does not alter the renderer's accepted behavior. The third run passes after that fix. The fourth changes to the precise explicit sRGB source contract and passes all controls. Original raw LLVM headers are retained alongside normalized IR, and normalization tests preserve every nonheader IR byte.

Six new tests cover strict parsing, whitespace and geometry bounds, unsupported holdouts, code-generator input validation, controller flag compatibility and metadata-only IR normalization. The full suite passes 221 tests. Acquisition/generated artifacts remain local; sanitized run anchors and counts are published.

## Remaining acceptance

This establishes a tiny custom source-fragment-to-IR-to-WASM path and opaque rectangle agreement on macOS V8. It does not establish execution on a browser or non-Apple host, the new source modules in a second interpreter, arbitrary Swift/SwiftUI compatibility, native Canvas IPC, hot reload, font/layout/state support or performance. F1's broader subset and F2's intended non-Apple host acceptance remain open. Next: execute the same sealed module on an available non-Apple host/browser, or independently verify it in the existing second interpreter; expand only with explicit feature/holdout and native reference evidence.
