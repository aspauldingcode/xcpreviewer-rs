# Browser primary-source adapter: implemented, execution blocked

The actual-browser adapter and owned page are implemented for the pinned 16 primary-layer source-derived standalone/checker modules. The page fetches and hashes the real WASM, runs two strides and two fresh instances per module, copies every 16,384-byte allocation and submits exact observations to a bounded loopback verifier. Two fresh page loads must produce identical payloads. The verifier independently recomputes the Fraction source-over expectations and compares every byte against the frozen macOS and applicable native callback targets.

The browser boundary explicitly converts premultiplied RGBA into straight RGBA with integer half-up unpremultiplication, then uses alpha-enabled sRGB `ImageData` and Canvas2D readback. Readback must equal the independently converted bytes exactly. This is a predeclared hypothesis, not an observed browser result. Native getter/PNG differences remain separate.

Planned acceptance inventory across two loads:128 frames/2,097,152 complete allocation bytes;128 invalid renderer requests/2,097,152 unchanged allocation bytes;199,648 Canvas2D bytes;40,320 reused native callback prefix bytes;320 checker controls including256 exact-one faults;32 aggregates;128 invalid checker index/mutation sentinel returns. Browser invalid checker tests do not claim whole-memory no-write evidence; that boundary was measured separately on Linux.

Unit fixtures verify rejection of pixel/alpha/padding/tail corruption, malformed inventories, stale nonces, module changes, boolean integer metadata, invalid-request writes, checker count changes and Canvas/straight-conversion corruption. These fixtures are synthetic tests, not browser observations. The page has no native Apple dependency. Source-to-C/LLVM compilation remains the pinned macOS operation; no Linux Swift frontend, arbitrary SwiftUI, native Canvas protocol, Windows or cost claim follows.

## Execution prerequisite

Computer-use inventory reported: `The Mac is locked and automatic unlock could not unlock it.` Native apps were unavailable; in-app browser inventory contained no tabs. The actual browser controller launch was rejected by automatic approval review because the Mac is locked and the browser prerequisite is unavailable. The rejection explicitly prohibited an indirect execution workaround. No browser experiment ran, no runtime manifest exists for this task, and no evidence was synthesized through Node, headless browser or a different launch route. No Xcode window or browser tab was opened.

Resume requires the user to unlock the Mac, followed by an available browser prerequisite and approval for the blocked action. The graph keeps browser research incomplete and blocked on that external change. Independent source/IR work can continue while it is blocked. F2 and both milestone acceptance contracts remain open.

Source anchor: `20261010T191804Z-portable-primary-source-subset-811cf568`, manifest SHA-256 `45f7ac0b391eb74b2580209a237e231ee77d55be31c2857129c14137d69b3f88`.

## Independent verifier performance correction

The full verification suite was interrupted at its five-minute work budget. Its retained traceback identifies the complete checker-memory corruption test repeatedly expanding every equal byte in `bytes_equal`; no browser action was involved. The comparator now checks equality of each complete 64KiB chunk using native bytes comparison after hashing/counting all bytes, and expands per-byte diagnostics only for unequal chunks. No bytes are sampled or normalized. An independent exhaustive comparator tests empty files, chunk boundaries, multiple equal chunks, bit flips and longer/shorter tails; hashes, byte/bit counts, mismatch offsets and bounded diagnostics must be identical. The interrupted run is not reported as a passing suite. This optimization addresses independent verifier work while the browser prerequisite stays blocked.

Final full verification:311 tests pass in61.670 seconds; browser page JavaScript syntax check passes. This is verification-suite evidence, not browser/runtime acceptance or a controlled product performance benchmark.
