# Native failure-action callback and capture lifetime

Static expansion remains paused. Two fresh owned-process runs each passed four native controls: unfulfilled and fulfilled owner destruction, on the main thread and on a worker. This exercises the existing failure-mode test(action:) case rather than replaying its source branch.

Minimum existing-case qualification resolves field record 0 at descriptor 0x1581a4 to `yyYbc6action_t`, runtime type `(action: @Sendable () -> ())`, size 16. A real compiler-created capturing Swift closure is initialized into the known consuming enum argument slot. No invented function/context pointer, new native function discovery or broad static inventory was used. Input metadata/image qualification is recorded in input-qualification.json.

| Native control | Actual observed outcome |
| --- | --- |
| Unfulfilled release, main | Failure action ran once synchronously within release; observer callback did not run; both owned FDs were open inside action; both contexts/FDs cleared before release returned |
| Unfulfilled release, worker | Same outcome, with action and destruction on releasing worker thread |
| Fulfilled before release, main | Observer callback ran during invalidate; failure action never ran; observer context cleared, but action context stayed alive until owner release |
| Fulfilled before release, worker | Same outcome; action context destruction occurred on releasing worker |

The action closure captures its own Probe strongly and only the observer's integer FD, not the observer Probe. Consequently, the action does not artificially retain the observer context while checking its resource. Explicit deinit events show observer destruction after the action in unfulfilled controls. Checked weak references and fcntl EBADF queries complement the logs. Exact relative destruction order of the two contexts is not generalized beyond observed boundaries.

## Ownership and threading

Caller closure/context references are dropped after native handle construction. Both contexts remain alive at that point. In fulfilled controls, the observer is released during invalidation but the captured failure-action context is still alive afterward. Owner destruction subsequently releases that capture even though the failure action is skipped. This directly distinguishes observer storage cleanup from failure-policy capture cleanup.

Probe uses checked Sendable conformance and immutable fields. The worker consumes a single native +1 reference through an internally locked lease; no main-thread release competes with it, and the main thread joins before weak/FD checks. The sole unchecked Sendable type is the lock-protected lease slot. GCD is used for synchronous native ABI/thread identity controls, not as a claim that the inherited harness is a strict Swift 6 migration. No actor/async scheduling behavior is inferred.

## Reproduction and evidence

Run `python3 tools/re/native-canvas-action-runtime/run.py --output /private/tmp/canvas-action-fresh` from repository root. Existing adapters pin PreviewsFoundationHost full SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d`, loaded path/UUID `6b75229bde5d3d3794bc75af4f4704c6`, known metadata sizes and symbol offsets. Native sessions hold the exclusive controller lock. Compiler stages are bounded to 30 seconds; each owned native process to eight seconds with owned process-group cleanup. The worker join also has a two-second bound.

initial/ and reproduced/ preserve exact executed original sources, adapters, verifiers, compiler/process receipts and JSONL traces. Both captures pass. Six semantic altered-trace controls reject: missing action, action after fulfillment, wrong action thread, early capture release, premature observer FD closure and incomplete cleanup. Sequence/timestamps are normalized so semantic checks—not accidental numbering errors—reject. These mutations are not additional native executions. No native failure, crash or timeout occurred in the qualified runs.

## Limits

This verifies failure-action invocation/skip and captured owned-context/FD lifetime for four controls in this image/profile. It does not qualify arbitrary closure captures, thrown errors (the action has no arguments and is nonthrowing), recursive destruction, general concurrent owner mutation, native transport/Mach/IOSurface resources, Preview.update, rendering, SwiftUI continuity or cross-platform WASM. Earlier log/assertion controls remain separately scoped. No Frida/logging probe, user Xcode/project access, unchanged native-window retry, system protection or preference change occurred. No Apple binary/raw private dump is published; no Rust product change or Rust test. Full native areas remain 0/9; tracked delivery remains 1/26 (3.8%).
