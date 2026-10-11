# Metal submission lifetime and destruction callbacks

After dropping both explicit CPU buffer and command owners and draining their construction pool, submitted retained-reference work keeps both weak objects alive through an event-blocked wait. Explicit event release produces one completed callback and the expected entire allocation. An unsubmitted command instead disappears, but its destruction invokes its registered completion handler once with status 0. Handler invocation alone is therefore not evidence of successful GPU work.

## Competing predictions and retained failures

Parent owner/pool discriminator seal: `7010b2175304947e02a515d44d895e02487dbc512da04a0ab7b6c3aad708db63`. This experiment moves from unsubmitted encoding with a CPU command owner to queued work after both CPU owners are removed. Only default `retainedReferences=true` commands are submitted. No unretained expired-buffer work is executed.

The initial prediction expected no unsubmitted callbacks. Both baseline native runs contradict it: dropping the unsubmitted command and draining the construction pool invokes the handler once, despite event value 0 and no submission. The original observer hid that callback status behind a null field. The failed prediction, original observer, actual waits, outputs and assessment with acceptance false remain in `baseline/`. The changed observer records the callback status even for unsubmitted destruction. Both changed runs observe status 0, event 0, null output frame, weak command/buffer nil after construction pool. This is a destruction callback observation, not a GPU completion or cancellation wire claim.

A preceding sandbox helper exited 2 at the device prerequisite before queued work. Empty output, actual wait, compile/environment and false acceptance assessment remain in `sandbox-failure/`. Native execution changes that access prerequisite, not source/deadlines. Four native helper executions then exit zero, two baseline and two changed; compile and subprocess deadlines stay 15 seconds, helper alarm 12 seconds, bounded event wait 20ms and completion wait 5 seconds.

## Submitted control and ownership boundaries

Each mode owns a queue and shared event outside a nested construction/encoding pool. A shared 16-KiB buffer is initialized entirely to `0x5c`; a default command waits for event value 1, then fills 44 active bytes in each of six rows at stride 256 with `0x77`. The encoder, buffer and command CPU strong variables are removed inside the nested pool. The submitted mode commits before command removal. After pool drain, only submitted work keeps both weak objects alive.

Submitted work times out at the 20ms semaphore wait with zero callbacks and event 0. The helper always sets its owned event to 1 before assessing the negative wait. It then waits at most five seconds for one callback with status 4. Only that completed handler promotes the weak buffer and copies the full allocation into independent data. Its temporary observer ownership is explicit; no CPU data is read while GPU work is pending. The token matches the original buffer. Independent expected bytes check all 16,384 bytes, including row padding and tail, rather than just 264 modified bytes.

After the outer queue/event pool drains, weak buffer is nil in all four native submitted cases. Weak command liveness is variable: the changed run 0 reports nil and changed run 1 reports alive. This observer does not require weak command nil or identify asynchronous internal holders. Callback completion is not a guarantee that every internal command owner has been released. Weak nil measures an Objective-C object lifetime boundary, not physical/kernel allocation reclamation.

## Provenance and independent verification

Native environment: macOS 26.5.1 (25F80), Xcode 26.6 (17F113), arm64, Apple M1 unified memory. REA package/server 6.2.0 independently binds owned baseline artifact `f2084ff01cb3b5464f0d0bd287e49b47f97a2c24027169020cef601cef744ea7` (`ev_4f389738055a7a034e85bce8cf7a0cd81ce3219d13240d11c00c49ae492aed0f`) and changed artifact `8ede3fec7711581336700d406d72a11ed34b02e100aba820cd1eeb67eecf0356` (`ev_d868dec8e399f73e56ecd2be4a315d8fe2855f3fc7e38b7be8962dd1ba3b1d50`). REA utility provenance and compact server identity are retained; all owned REA target sessions close. Static artifact identity and the subprocess runtime measurements remain distinct. Executables stay local.

The independent reader verifies actual waits, retained failures, metadata, scoped weak predicates, destruction status versus completed status, timeout/callback ordering and 196,608 complete independently expected bytes across four native runs. Six resealed faults alter exit, destruction status, timeout, pending owner, early callback and padding byte 44; all must fail despite valid replacement hashes. The current helper source must match the frozen changed source. Candidate checks also verify the parent owner controls in isolation.

Evidence: `research/evidence/gpu-submission-lifetime-2026-10-11`; manifest `d8500f8f4038a772748b22e68233a7316640fc3c079e1e5e1c14c02b3aa0c9a1`. Reproduce with `xcrun clang -Wall -Wextra -fobjc-arc -framework Foundation -framework Metal tools/re/gpu_submission_lifetime.m` under the exclusive controller lock and retained deadlines.

## Remaining acceptance

This finite public Metal control supports submission retention and distinguishes destruction handler invocation from successful completion. It does not establish automatic deadline cancellation, final physical release, cross-process IOSurface/Mach failure accounting, or actual Canvas protocol behavior. R1/R2 and both milestones remain open. The approved private Xcode bridge remains offline; no restart or workspace was opened.

Do not repeat unchanged pool/submission controls. Next select required peer-failure accounting or a demanded portable product contract; any consumer of completion callbacks must check terminal status rather than handler count alone. The bridge restoration prerequisite remains separate from available REA.
