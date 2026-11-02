# Observer-token removal and cleanup ordering

Pinned arm64 PreviewsFoundationHost source qualification. Original readers, hashes and sanitized findings only. Raw Apple instruction text remains temporary and local.

The reader verifies 860 instruction bytes and fifteen selected calls across the cancellation closure, waiting-state helper, removal callback, dictionary removal, optional observer cleanup and OverfulfillHandle cleanup. Native state/storage reflection independently binds legal case order.

The token closure acquires a strong handle from weak storage. Missing owner returns. Live owner loads state and locks around updateWaitingState. Fulfilled state skips the mutation callback and returns alreadyFulfilled; waiting invokes the removal callback, commits modified storage and remains waiting. After unlock the closure releases its acquired owner and destroys the update result.

The removal callback uses the captured Identifier. Dictionary miss returns nil. Hit performs dictionary uniqueness/copy delegation, extracts/deletes the value and removes the matching ordered key. An inconsistent key array traps. Copy/delete/array-remove internals are not fully recovered in this unit.

Returned optional observer storage is destroyed inside the callback, before outer unlock. If present, that helper releases its closure context; absent returns. This is a source ownership boundary, not proof that reference count reaches zero or that deinit/reentry occurs under the lock. Actual cancellation, registration/creation, repeated cancels, concurrency, handle invalidation and final settlement remain unobserved.

OverfulfillHandle cleanup separately destroys failure-mode storage and releases a context reference. Its complete small body has no direct failure-policy call. Released-context effects and failure-mode destructor internals remain opaque.

Exploratory ranges included adjacent bodies; final qualification boundaries exclude them. REA identity aligned/no open session; prior UI/Ghidra failures not retried unchanged. Run `python3 verify.py` against pinned Xcode with access to the exclusive repository controller lock. Disassembly has twenty-second bounds per range; fresh copied-reader complete-findings replay has a fifty-five-second bound. No native private call, GUI change, product change or Rust-test rerun. Full acceptance remains open.
