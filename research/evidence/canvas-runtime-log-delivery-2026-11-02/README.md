# Qualified native log input, backend record and observer effects

Static expansion remains paused. The prior zero-filled log-associated attempt remains excluded in [earlier failure-policy evidence](../canvas-runtime-failure-policy-2026-11-02/README.md). This package qualifies the missing input interface and exercises real native logging, with separate attached and unattached controls.

## Minimum interface qualification

The existing FulfillmentFailureMode field descriptor at 0x1581a4 has five records. Only the already recovered log case's associated type was read: `SS7message_t`, resolved by the native Swift runtime as `(message: Swift.String)`, size 16. Full pinned PreviewsFoundationHost hash/UUID checks precede the read. No new functions, decompilation or broad static inventory were added.

The new input uses a real compiler-constructed Swift short string `owned-policy`, copied into the known associated-value slot with marker 1. It is not an assumed nil/logger pointer or zero-filled String. The short-string bound avoids claiming untested heap-backed String transfer/ownership. The existing constructor/observer/owner-release adapters and image profile remain unchanged.

## Native results, two fresh complete runs

Each run used the same owned binary for six controls: fulfilled/unfulfilled release without hooks, fulfilled/unfulfilled with a stdin gate but no attachment, and fulfilled/unfulfilled with the gate plus Frida observation. All returned zero with checked owned context/FD cleanup. Unfulfilled controls had no observer callback; fulfilled controls invoked it before owner release. No native crashes/timeouts occurred with the qualified inputs.

| Observation condition, unfulfilled release | Observed result |
| --- | --- |
| No attachment | Readable matching-PID unified-log Error record from PreviewsFoundationHost |
| Stdin gate, no attachment | Same readable native record; the handshake alone did not reproduce the composition failure |
| Frida entry-only logging API probe | Native log-enabled check returned 1; `_os_log_impl` entered from caller offset 0x2be2c with type 16; process returned normally; stored record was `<compose failure [missing precomposed log]>` |

The readable unattached message was `FulfillOnce failure: owned-policy, callsite: owned:1:1 within owned`, subsystem com.apple.dt.Previews, category uv. Queries were bounded/read-only and selected exact owned PIDs plus owned message text. Only selected sanitized records are published, not full log-store output. This proves immediate backend record retrieval for these controls, not long-term persistence, crash durability or every logging configuration. Receipt field `os_log_persistence_verified` has that narrow immediate-retrieval scope.

Fulfilled attached controls reported hooks ready but no selected policy logging calls; their callbacks/cleanup still completed. Absence is scoped to the selected native failure-function caller range, not all logging in the process. Native logger checks and API calls are observations; no API arguments, results or preferences were changed by the agent.

## Instrumentation limitation preserved

An earlier entry/return probe also observed the native API call and return but produced an unreadable compose-failure record while its unattached counterpart logged readable text. That comparison is retained under entry-return-probe-comparison/. Removing the logging API return hook did **not** restore readable attached output. The final entry-only probe and gated unattached comparison reproduce that distinction. This is an observer-condition effect in this setup; the precise mechanism was not established. No native logging defect, general Frida defect or specific return-address explanation is claimed.

Consequently, logging-delivery claims use **unattached** native backend records. Attached probes establish API entry/caller/enablement only. Normal process return alone is not proof of correctly composed or delivered log text. The earlier unqualified input's SIGSEGV is not reclassified as a native bug or silently upgraded to a valid control.

## Reproduction, assertions and boundaries

Run `python3 tools/re/native-canvas-log-runtime/run.py --query-log-store --output /private/tmp/canvas-log-fresh`. It pins on-disk hash/loaded path and UUID using the existing native adapter, qualifies the one associated type, builds owned code, executes controls and queries owned log records. Compiler stages are bounded to 30 seconds, native processes to eight seconds after gate release, Frida stages separately bounded; the runtime controller lock is exclusive. Only owned child process groups can be killed/reaped on failure. No user Xcode/simulator/project or system protection/preference was accessed.

initial/ and reproduced/ preserve exact executed sources, verifiers, process receipts, hook messages and selected log records. Final root verify.py additionally checks selected record PIDs against process receipts on those same traces; original executed verifiers remain frozen. Six synthetic mutations reject: associated type, enablement, caller, unexpected fulfilled API call, missing readable record and mismatched record PID. These are verifier controls, not more native executions. Both final native/store assertions pass. Raw binaries, object/cache files and private log/register dumps are excluded.

Still unknown: heap-backed log strings, test-callback policy, soft-assert delegate delivery, general observer transparency, native Canvas transport/render cleanup, Preview.update, SwiftUI continuity, true auto-resume/state gates, other targets/hosts and standalone WASM parity. Native-window failure was not retried. No Rust product change or Rust test. Full native area acceptance stays 0/9; tracked delivery stays 1/26 (3.8%).
