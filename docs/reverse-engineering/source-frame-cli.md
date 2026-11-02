# Supported source-to-frame preview CLI

The preview CLI builds the declared three-primary-layer source subset, runs its
import-free WASM renderer in a bounded Node process, verifies the complete raw
allocation and writes a PNG. The [sample expression](../../examples/primary-layers.swift)
is ready to use. It supports the existing explicit sRGB primary colors, alpha
eighths, the two declared layer orders and dimensions from 1 through 64.

From the repository root, using the installed toolchain:

```sh
research/venv/bin/python tools/re/preview_cli.py examples/primary-layers.swift \
  --cache research/build/preview-cache \
  --output research/build/preview-output \
  --clang /Users/8amps/Library/Developer/Toolchains/swift-6.3-RELEASE.xctoolchain/usr/bin/clang \
  --wasm-ld /Users/8amps/Library/Developer/Toolchains/swift-6.3-RELEASE.xctoolchain/usr/bin/wasm-ld \
  --node /etc/profiles/per-user/8amps/bin/node
```

The command prints one JSON result and returns zero on success. `current.json`
selects the last successful bundle. Its `png` and `allocation` paths are relative
to the output directory. The receipt records source/module/frame/image hashes,
dimensions, stride and the manifest anchor. Call `verify_bundle` before consuming
a saved bundle. Use `--stride` for explicit row padding and `--runtime-seconds`
for a runtime deadline up to ten seconds; the default is five seconds.

Each bundle retains source, lowered C, normalized LLVM IR, WASM, a 16384-byte raw
allocation, PNG, runtime identity and logs. Runtime checks enforce no imports,
the expected exports, two memory pages, the fixed allocation and exact render
extent. Four invalid strides must preserve every allocation byte. A Fraction
oracle compares all active bytes, padding and unused tail before publication.

Raw pixels implement the scoped premultiplied callback-target contract. PNG
stores straight RGBA with an sRGB intent chunk. Conversion sets RGB to zero at
zero alpha and otherwise computes `floor((premult * 255 + floor(alpha / 2)) / alpha)`.
This is the declared PNG policy; native getter/export quantization can differ.
General Swift compilation, native Canvas transport, a browser, state migration
and a hot-reload watcher remain separate work.

Compilation reuses the existing identity-bound source cache. Frame publication
has its own lock, immutable version directory and atomic pointer. Unsupported
source, invalid stride, bad cache data, failed/timed-out runtime and a
pre-publication fault preserve the last good pointer and image. Temporary frame
directories are removed on return. Local hash consistency does not authenticate
a cache against replacement of all of its files and anchors.

`primary-source-frame-cli` is a graph research task assisting I5. Its reviewed
`source_frame` adapter executes actual CLI builds/renders, compares anchored
native callback-prefix references, decodes PNGs with an independent library,
and exercises failure preservation. Passing this scoped task does not close
the I5 delivery contract or either milestone.

## Verified checkpoint

The graph-selected sealed campaign passes sixteen actual CLI frames over four
source/geometry/order cases, two stride settings and two repeats. All 262,144 raw
allocation bytes agree with independent predictions. Four frames also match
2,880 bytes of anchored native callback-target data. Pillow decodes all sixteen
PNGs and compares 70,448 straight-RGBA bytes against a separate Fraction projection.
Sixty-four invalid renderer requests preserve their complete allocations.

Six negative controls preserve the previous pointer and PNG: unsupported source,
invalid stride, runtime exit failure, corrupted cached module, publication fault
and an owned timeout. All 338 repository tests pass, including deliberate active,
padding and tail corruption, PNG literal controls, locks, symlinks and a staging
rename/accounting regression. The sandbox preflight failure and the artifact scan
failure remain sealed. The repaired controller handles vanished directories
during atomic publication while retaining access failures.

See [evidence and manifest anchors](../../research/evidence/source-frame-cli-2026-10-10.json).
The graph marks only this scoped research task complete; independent delivery
review and both milestones remain open.
