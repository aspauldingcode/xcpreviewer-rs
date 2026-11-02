# Fulfillment failure-policy dispatch

Pinned arm64 PreviewsFoundationHost static qualification. Original readers, hashes and sanitized findings only; raw Apple instruction text stays temporary and local.

Verified 1,328 instruction bytes, nine selected calls, native enum cases and five legal source dispatch routes. Bounded instruction interpretation checks representation predicates; it executes no native callbacks and is not an independent behavioral oracle.

- test invokes its stored closure; effects depend on that callback.
- log conditionally emits an error-level message containing callsite information.
- softAssertDebugOnly reaches error/callsite logging with NSError bridging in this pinned shipped image. This branch has no call to _assertionFailureBase; no cross-build/version claim follows.
- softAssert delegates to local _assertionFailureBase at 0x71290. A return epilogue follows if that delegate returns; its assertion/process effects remain unqualified.
- fatalError formats error text and calls Swift's standard _assertionFailure returning Never. No crash or assertion was triggered.

This extends the recovered token constructor softAssert policy and waiting-state deinit call chain. It does not establish actual last ownership, assertion delivery, effective logging, cancellation, resource settlement or full Canvas parity. REA identity aligned/no open session; prior UI/Ghidra failures not retried unchanged.

Run `python3 verify.py` with pinned Xcode and exclusive controller lock. Disassembly is bounded to twenty seconds; fresh copied-reader complete-findings replay to fifty-five seconds. No native private call, GUI/system change, product change or Rust-test rerun.
