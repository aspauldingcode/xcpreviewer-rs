# Observer registration and cancellation tokens

Pinned arm64 PreviewsFoundationHost static qualification. Original readers, hashes and sanitized findings only; raw Apple instruction text stays temporary and local.

The reader verifies 1,660 instruction bytes, seventeen selected calls and native token/state/outcome fields. Waiting registration inserts an observer while holding the handle state lock, then unlocks and creates a cancellation token. Already-fulfilled registration unlocks, invokes the supplied observer with the existing trace and returns no token. This establishes source call order, not actual delivery.

The insertion helper obtains an Identifier from a separately locked counter and delegates dictionary update. Counter wraparound, process namespace and dictionary update internals remain unqualified. The returned token captures a weak owner box and Identifier. The capture forwarder reaches the previously recovered removal closure. A weak edge here does not rule out user callback reference cycles.

The concrete token constructor stores callback and onceGuarantee reference. Token.cancel locks its once guarantee, delegates fulfillment and unlocks. Outcome 1 skips callback; otherwise it delegates callback invocation, whose concurrent specialization invokes the closure pair. Included fulfillment code binds waiting outcome 0 and normally returning already-fulfilled outcome 1. Complete constructor failure policy, exceptional paths and token deinit auto-cancellation are not established.

No actual registration/cancel/repeat, weak-owner-loss, race/reentry or final resource-settlement control ran. Full acceptance remains open. Exploratory forwarding included adjacent unnamed trampolines; final qualification excludes them. Prior UI/Ghidra failures were not retried unchanged.

Run `python3 verify.py` against pinned Xcode with the exclusive controller lock. Disassembly has twenty-second bounds per range; fresh copied-reader complete-findings replay has a fifty-five-second bound. No native private call, GUI/system change, product change or Rust-test rerun.
