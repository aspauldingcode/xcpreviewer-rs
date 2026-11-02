# Invalidation state ownership and dispatch

Pinned arm64 PreviewsFoundationHost source qualification. Original reader, hashes and sanitized findings only; no Apple instruction text or binary is included.

The reader verifies 1,772 instruction bytes and twenty selected calls across the handle initializer/deinit, state-owner deinit, explicit invalidation specialization and protocol witness. Reflection and native field-offset symbols independently connect the handle's state reference to `FulfillOnceState<ObserverAndTokenStorage<ConcurrentInvalidationObserverBox, InvalidationTokenCallback>, InvalidationTrace>` and its lock-backed waiting/fulfilled state.

A handle release does not prove last ownership. If state deinit runs, it peeks the lock-backed state. The fulfilled branch skips unfulfilled-error construction. The waiting branch can evaluate the optional initialization-info closure, constructs an Unfulfilled error and invokes the configured failure policy. The policy's effects and concrete configured mode remain unqualified. Initialization-info callback effects remain opaque; no actual cancellation is established.

Explicit invalidation forwards through the protocol witness to a concurrent specialization. It locks around a fulfill helper, unlocks and releases the state reference before dispatching extracted observer closures. The managed-token loop separately locks each token state around another fulfill helper, unlocks, then conditionally invokes its callback. Returned discriminator 1 skips that callback. Helper transition internals, delivery effects, reentry/deadlock behavior and actual lifetime/resource settlement remain open.

Exploratory ranges included adjacent bodies; final source ranges stop at the appropriate function boundaries. Adjacent failure-policy implementation is not included in the semantic claims. Prior locked-screen/Accessibility and Ghidra failures were not retried unchanged. REA server identity aligned and no binary session was open.

Run `python3 verify.py` on the pinned installed Xcode with access to the exclusive repository controller lock. Disassembly is bounded to twenty seconds per range; fresh copied-reader complete-findings replay to fifty-five seconds. No native private call, GUI action or product change; no Rust suite rerun claimed. Full recovery acceptance remains open.
