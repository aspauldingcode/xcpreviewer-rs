# Cancellation callback boundaries

The pinned PreviewsFoundationHost image exposes two callback wrappers: isolated and concurrent. Their actual invoke bodies dispatch stored closures. This narrows the generic cancellation action boundary without assigning a fixed transport effect to every token.

Baseline: Xcode 26.6 (17F113), macOS 26.5.1 (25F80), arm64; image SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d`. The previously published cancellation-entry seal was verified against its committed manifest anchor before reuse. New worker image hashes match this baseline.

## Discriminating observations

The isolated constructor at `0x129770` stores four incoming words in the result and places its state reference at offset `0x20`. The concurrent specialization at `0x129858` stores a pair and places the state reference at offset `0x10`. Both selected constructors initialize the separately allocated state object's lock word at `0x4c` and byte at `0x49` to zero. These are static stores, not native allocation/lifetime measurements.

At `0x1299f4`, isolated invoke loads an optional actor pointer and a closure/context pair. A null actor branches from `0x129a0c` directly to context setup at `0x129a4c`; otherwise it calls `Actor.verifyIsolated` at `0x129a48` before invoking the stored closure at `0x129a50`. Closure invocation uses the saved context, rather than the actor pointer, as the Swift context register.

Concurrent invoke at `0x129a64` loads its stored closure/context pair at `0x129a70` and calls that closure at `0x129a74`. Its eight-instruction body has no direct call to an isolation helper.

A dependent experiment recovered `verifyIsolated` at `0x114e38`. Its single call at `0x114e5c` targets the Swift `preconditionIsolated` stub at `0x12feb4`; normal return occurs at `0x114e68` if the callee returns. The wrapper does not expose an executor hop. Runtime executor checks, failure behavior and callee side effects remain unexecuted.

## Verification and publication

Two bounded disassembly controls validate these selected boundaries. Synthetic corruptions alter the callback context, optional-actor branch, isolation callee, constructor initialization, direct-call target, helper extent and duplicate instruction evidence. Missing or duplicate bodies fail. These are finite pinned pattern checks, not general control-flow or Swift ABI proofs. The isolation checker was tightened to check the direct-call target as well as its stub annotation; both passing seals remain retained.

Five new runs are sealed and verified with the manifest anchors published in [sanitized evidence](../../research/evidence/cancellation-callbacks-2026-10-09.json). The complete suite passes 131 tests. Raw Apple disassembly remains local; published files contain owned checker code, synthetic controls and scoped observations.

R2 remains open. Runtime witness-table relocation and the association between a generic token's indirect action and these concrete wrappers still require independent evidence. The selected caller closure must be recovered before assigning an actual cancellation effect. No claim of automatic transport cancellation, abandoned-reply completion, concurrency correctness, resource release or full Canvas lifecycle follows from these wrappers. No Xcode windows were opened, no process attached and no private Swift ABI constructed.
