# Preview bitmap construction and portable import

Direct GhidraVibe recovery of the current PreviewsMessagingHost BitmapDescription.makeImage function (0x4a6f4, 432 bytes) was checked against ARM64 instructions. It bridges Data into a CGDataProvider, creates the named color space, and calls CGImageCreate with the decoded width, height, bitsPerComponent, bitsPerPixel, bytesPerRow and bitmapInfo. Decode pointer is null, interpolation false, rendering intent default. Three distinct nil/error branches occur after provider, color-space and image creation, with stored error discriminants 0, 1 and 2 respectively. Names and complete runtime error propagation are not claimed recovered. Raw decompilation/disassembly remains local; identities and hashes are retained here.

REA6.2.0 target binding matches SHA-256 0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c, ARM64. GhidraVibe0.1.1 / GhidraMCP5.14.2 returned the same program path and architecture. The Ghidra Swift pseudocode has register/ownership artifacts; argument and nil-branch claims use instructions, not its invalid C pointer expressions. The REA session was closed and the exclusive analysis lock released. No Xcode MCP/bridge, private Swift ABI call, runtime attachment, UI or user-process operation was used.

## Native oracle and independent expectations

An original research-only C program uses the public CGImageCreate pipeline above, then draws at equal size into a public premultiplied RGBA8 sRGB bitmap context with copy blending and interpolation disabled. The inputs are original owned fixtures, not Apple dumps. Independent Python generation uses six explicit asymmetric RGBA pixels spanning alpha 0,1,127,128,254,255, two rows, source row padding and trailing bytes. Four explicit premultiplied byte layouts are checked: first/little (0x2002, BGRA), first/big (0x4002, ARGB), last/little (0x2001, ABGR), last/big (0x4001, RGBA).

For each format, CGImage's copied provider data matches all40 input bytes, including8 row-padding and8 trailing bytes. Native drawing matches every56 independently expected output bytes:24 active bytes,16 output row-padding bytes and16 allocation-tail bytes. The asymmetric rows detect row reversal. All4 native outputs match; there are zero byte mismatches. The oracle source, exact generation/verification script, native results and compiler/OS/SDK identities are included. Public SDK CGImage.h supplies the constants and declarations; no private declaration is invented.

## Reconstruction

The portable Rust BitmapDescription.write_premultiplied_rgba8 method imports the measured four-format 8/32-bit sRGB subset. It validates the entire request and all source pixel premultiplication before writing. It converts active pixels, preserves source bytes and destination row padding/tail, and returns the destination row extent. The decoded binary payload is connected through this method to a new render-preview-bitmap CLI producing tightly packed premultiplied RGBA8 bytes.

All26 Rust tests pass (23 prior and3 new integration suites). Each4-format decoded plist reproduces all56 native and independent expected output bytes. Additional controls cover bad geometry/stride/length, arithmetic/resource limits, unsupported flags/color/bit depths, late invalid premultiplication, tight output and padding/tail independence. Every rejected request preserves the entire destination. The CLI's4 tight24-byte outputs separately match native/independent active bytes. Unsupported input exits1 and preserves a previous output file. This is validation-failure preservation; atomicity on filesystem write failures is not claimed.

From the repository with an installed Rust toolchain:

```sh
cargo run --offline -p canvas-core --bin render-preview-bitmap -- tools/re/rust/canvas-core/tests/fixtures/bitmap-image/2002.bplist /tmp/preview.rgba
```

The output is premultiplied RGBA, not straight-alpha image-file data. No image encoder or SwiftUI view renderer is implied by this command.

## Scope and remaining work

These are direct shipped-code construction findings plus an actual public CoreGraphics oracle and working original portable import. They do not prove native Canvas transport capture, live interaction, refresh/state behavior, IOSurface resource release/reuse, general color management, Display P3, HDR/float or alternate alpha formats. Native drawing here is an isolated equal-size public API oracle, not an observed private Canvas draw. Source geometry is restricted to positive dimensions up to16384 and64 MiB extents. Full source rows must exist, premultiplied channels must not exceed alpha, and unsupported color spaces/flags return explicit errors. These validation policies are conservative original choices rather than Foundation/CoreGraphics malformed-input parity.

Both milestones and native R1/R2 gates remain open. Next trace the consumers of makeImage/selectableRegions into lifecycle/refresh/input, correlate native observations through a changed permitted instrumentation route, and connect accepted pixel/state behavior to the developer canvas. Prior binary-input evidence and all pinned source blobs at commit6658acb93863dab9e8dec168eb9d931ad7b2108a were reverified before this seal.
