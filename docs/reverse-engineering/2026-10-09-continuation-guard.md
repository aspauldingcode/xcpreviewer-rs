# Static continuation completion guard

The [encoded reply initializer](2026-10-09-transport-reply.md) constructs PreviewsFoundationHost.Continuation. Five dependent bounded native probes follow its public resume method, initializers, captured callback closure and exact unit-state fulfillment specialization. Foundation image SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d`, UUID `6b75229bde5d3d3794bc75af4f4704c6`; prior reply anchors verify. [Sanitized evidence and five manifest anchors](../../research/evidence/continuation-guard-2026-10-09.json) retain source/artifact verification.

## Observed guard

Public Continuation.resume(with:callsite:) forwards through its stored callback pair; the guard resides inside the initializer-owned callback closure. That closure acquires an os_unfair_lock, calls the unit-state FulfillOnceState specialization, unlocks, reads the outcome tag and skips user resume when tag equals 1. The user callback is outside the lock.

The exact specialization reads a state byte at offset 0x39. The first-fulfillment path stores flag 1 and writes outcome tag 0. The already-fulfilled path calls an overfulfill handler and writes outcome tag 1 on normal return. Combined with the closure branch, this statically supports intended suppression of repeated user callbacks after the first state transition. The overfulfill diagnostic runs under the surrounding lock; policy effects such as logging, assertions or thrown errors remain unmeasured.

This distinguishes a per-instance locked completion guard from a mere stored callback or identifier-based correlation. It does not prove every Canvas completion uses this path, recover cancellation mapping, or provide native concurrent/reentrant execution evidence.

## Verification and limits

The disassembly adapter now has an explicit guard_control mode. Its fail-closed scanner requires unique lock/fulfill/unlock/callback sites in order, the same observed lock identity, the exact outcome discriminator and a branch to the reviewed callback-skipping epilogue. It refuses missing/duplicate lock evidence, changed lock identity, discriminator changes and callback-bypass changes. This is structural validation of the observed guard, not a general ARM64 interpreter or native once-only execution test. State-function outcome meaning is separately scoped analyst instruction analysis.

All 115 tests pass. All five runs seal and verify against the pinned image hash. No private Swift ABI declarations or process attachment were used. The framework has no Modules directory at the inspected location, so a safe typed runtime constructor is not established. Raw Apple disassembly stays local; no Xcode windows opened.

Next obtain a reviewed typed native runtime/observation boundary for duplicate, concurrent and reentrant completion plus failure-policy behavior. Follow cancellation independently, and retain the live correlated-envelope gate. R2/P1/P2 and both milestones remain open.
