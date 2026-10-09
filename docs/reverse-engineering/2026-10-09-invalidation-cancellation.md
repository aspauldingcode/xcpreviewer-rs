# Invalidation cancellation: weak-owner and state gates

The pinned native invalidation-token closures expose two independent guards before an observer-storage update: a weak-owner check and a state-byte check. Neither establishes a fixed transport cancellation operation.

Baseline: Xcode 26.6 (17F113), macOS 26.5.1 (25F80), arm64. Foundation image SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d`. Prior callback/isolation seals were checked against their committed anchors; each new run reports the same image hash.

## Recovered boundaries

The isolated closure at `0x419cc` and concurrent closure at `0x41f10` hand off to a shared body at `0x41f2c`. The checker decodes their ARM64 B immediates independently of symbol annotations to verify this target.

The shared body weak-loads its owner at `0x41f70`; null at `0x41f74` branches to the epilogue at `0x41fc4`. If present, it locks storage at `0x41f8c`, calls the selected update function at `0x41fa4`, unlocks at `0x41fac`, releases the strong owner at `0x41fb4`, and dispatches result cleanup at `0x41fc0`. Lock and unlock both use the same base plus `0x54`. This is normal-return static ordering; exceptions, traps and native races remain untested.

Instruction-derived targets lead through concrete partial apply forwarders. Concurrent target `0x428d0` calls an `OrderedDictionary.removeValue(forKey:)` specialization; isolated target `0x42604` calls its optional-valued subscript setter. These target names and call boundaries narrow the investigation but do not certify the full dictionary operation. Result cleanup target `0x428fc` branches to `0x42648`, whose byte comparison conditionally tails `swift_bridgeObjectRelease`; this is not a measurement of resource reclamation.

Both selected update wrappers reach the merged body at `0xbeef0`. It reads the halfword at state offset `0x40`, extracts its upper byte (offset `0x41`) and compares against `1`. That path bypasses the indirect mutation callback at `0xbefd0` and writes result tag `1`. The other path invokes the callback, writes state byte zero at `0xbefe8`, and returns result tag `0` at output offset `8`. Declared enum case names are not assigned ABI tags from this finding alone.

## Controls and scope

Added a bounded disassembly control for the exact four gate/forwarder entries. Synthetic mutations change the weak-owner branch, lock identity, unlock target, state branch, skipped-callback destination, outcome tag, state offset, and encoded handoff target. Missing and duplicate bodies fail. This is a finite pinned boundary checker, not full Swift ABI interpretation or a general proof of all paths.

Four new runs are sealed and verified against the anchors in [sanitized evidence](../../research/evidence/invalidation-cancellation-2026-10-09.json). All 132 tests pass. Raw native bodies stay local; published files contain owned checkers, synthetic tests and scoped observations.

R2 stays open. Next recover the called dictionary implementation and selected-flow callback association, then obtain safe native runtime ordering/race observations. These static guards do not prove Canvas cancellation, abandoned-reply completion, Mach/IOSurface release or final physical reclamation. No Xcode windows were opened, no process attached, and no private Swift ABI constructed.
