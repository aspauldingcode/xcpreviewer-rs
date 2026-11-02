# Native owner destruction under recovered failure policies

Static expansion remains paused. Two qualified fresh owned-process runs exercised six controls each against the pinned shipped PreviewsFoundationHost. No Xcode process, project, simulator, UI or preference was accessed.

| Configuration | Unfulfilled owner release | Invalidate before owner release |
| --- | --- | --- |
| softAssertDebugOnly, marker 2 / payload 0 | Returned; no observer callback; weak context cleared and owned FD closed during release | Callback ran; context/FD cleared before owner release; returned |
| softAssert, marker 2 / payload 1 | Returned; no observer callback; weak context cleared and owned FD closed during release | Callback ran; context/FD cleared before owner release; returned |
| fatalError, marker 2 / payload 2 | Owned child SIGTRAP (-5), explicit unfulfilled-handle fatal diagnostic; no release-end, callback, context deinit or pass event | Callback ran; context/FD cleared before owner release; returned |

The fatal diagnostic was `Fatal error: concurrent invalidation handle was deallocated without being invalidated.` Both qualified fatal children terminated at that point and were reaped by the owned supervisor. No normal context/FD cleanup is asserted after fatal termination. OS-level reclamation was not independently measured.

The soft-assert-configured owner release returning is an observation in this pinned shipped image/environment. It does **not** establish assertion delegate invocation, UI presentation, assertion suppression policy or behavior in another build. Returning debug-only/soft cases do not establish logging delivery. The test callback policy and log-associated representation remain unqualified.

## Existing interface and execution qualification

Existing source evidence: [failure-policy dispatch](../canvas-failure-policy-2026-11-02/README.md), [state destruction](../canvas-invalidation-state-2026-11-02/README.md), and [owned native observer adapter](../canvas-runtime-validation-2026-11-02/README.md). No additional functions were recovered. The prior source enum dispatch identifies the marker-2 payload discriminants. The existing owned constructor adapter now receives those three representations. Each native process asserts loaded path/UUID `6b75229bde5d3d3794bc75af4f4704c6`, metadata and symbol offsets; the supervisor pins full file SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d`.

The exclusive controller lock covers native execution. Compiler bounds are 30 seconds each; owned native bounds eight seconds with owned process-group timeout cleanup. Both qualified runs completed without timeouts. The owner/context weak-reference and fcntl checks are in the executed original Swift source. initial/ and reproduced/ contain exact executed code/adapters, receipts and traces. Binaries, object files, module caches and raw Apple crash/register dumps are excluded.

Published native stderr is deliberately reduced to the fatal diagnostic line; stderr-redactions.json retains original local byte counts/hashes and the publication transformation. The assertion reader checks that diagnostic plus actual signal/PID/trace boundaries. Five altered-trace controls reject: fatal return status, missing fatal diagnostic, false FD cleanup, wrong policy and missing deinit. These synthetic mutations are verifier checks, not native executions. Both qualified traces pass.

## Excluded exploratory log attempt

The initial exploration also zero-initialized a marker-1 log-associated representation without qualifying its associated payload. Unfulfilled release terminated with SIGSEGV (-11); its sanitized matching-PID stack enters Swift String UTF8 formatting and FulfillmentFailureMode.fail. The fulfilled attempt returned but did not exercise that formatting path. **Neither attempt is accepted as valid log-policy behavior.** The associated payload representation was not qualified; the precise fault cause is not established and no native logging bug is claimed. This failure is retained under excluded-log-attempt/ with original owned source, process receipts, JSONL trace and selected crash metadata/frames; raw stderr/private dump remains local. The canonical runner excludes log and test cases rather than repeating the unqualified input.

## Remaining scope

No observer callback should be inferred on unfulfilled returning release: actual callback lists were empty. Returning controls observed exactly one owned context deinit/close; they do not establish all native state/closure allocations, transport/Mach/IOSurface resources or logging/assertion delivery. Fatal controls show where normal cleanup stopped, not a general resource leak. Existing Canvas build/file controls are separate; no Preview.update, rendered output, SwiftUI state or cross-platform WASM behavior was exercised here. Native-window limitations were not retried. No Rust product changes or Rust tests. Full native area acceptance stays 0/9; tracked delivery stays 1/26 (3.8%).
