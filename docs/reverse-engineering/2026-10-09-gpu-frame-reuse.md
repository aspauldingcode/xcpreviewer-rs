# Owned GPU frame reuse after timeout recovery

The audited receiving process now reuses the same imported IOSurface, Metal texture, destination buffer, queue and shared event across three completed frames. The first frame is the producer's original color; the receiver then renders the opposite color and restores the original. This gives R2 a GPU-backed counterexample to treating resource identity as frame identity, and extends the R1/R3 owned event recovery control.

Baseline: Xcode 26.6 (17F113), macOS 26.5.1 (25F80), arm64, Apple M1, shared BGRA8Unorm. The previous event-timeout seals were verified against their published anchors. The retained Xcode broker remains running/responsive, but no new native Canvas capture or transport observation is claimed.

## Ordered frames and independent predictions

After the original imported readback, two commands use the same queue, texture, destination buffer and event. Each encodes an event wait followed by render clear and texture-to-buffer blit. Event values advance from 0 to 1 to 2 to 3. Before each explicit signal, a 20ms semaphore wait must time out with no callback and a pending committed/scheduled command. The fixture always releases the event before assessing that negative control. A separate five-second deadline then requires one completed callback and no command error before CPU snapshots.

The receiver's texture has render-target and shader-read usage. Each new render changes all active pixels while preserving source padding/tail. The destination buffer is reused without reinitializing it between frames. Independent expectations require original/opposite/original opaque BGRA pixels, `0xa5` source padding/tail and `0x5c` destination padding/tail. A stale first-generation destination cannot pass the opposite-color expectation. The final original-color restore also must pass the existing peer CPU snapshot/mutation, clean/abrupt exit and retained-port/local-right cleanup controls.

Each helper records the imported surface ID, positive resource pointer tokens, generation order, event values, pending and completed statuses, callback counts and full source/destination allocations. The verifier requires all four distinct resource tokens to remain equal between generations and ties surface ID to the audit-verified receiver. These local tokens and generation indices are owned fixture evidence, not recovered native Canvas frame identifiers or cross-process GPU event handles.

Four geometries, clean/abrupt receiver exits and two repetitions give 16 helpers per campaign. The two added frames contribute four more full-allocation comparisons per helper: 192 comparisons total, or 3,145,728 bytes. All three reuse campaigns pass exactly. The previous single-frame event-timeout control passes after the shared helper signature and adapter changes.

## Rejection controls and remaining scope

Tests reject incomplete/reordered generations, changed or wrongly typed resource tokens, wrong surface IDs, event progression, callback counts, completion statuses, deadlines and Boolean flags. Independent stale-frame and active/padding/tail mutations also reject. Reuse mode requires reviewed consumer, producer and event-timeout flags. All 145 tests pass; four new seals are anchor-verified in [sanitized evidence](../../research/evidence/gpu-frame-reuse-2026-10-09.json).

Every pre-release sample in the reuse campaigns was committed status 2. This does not prove GPU arrival at the event instruction or separate scheduling delay from gate delay. Commands complete serially; no overlapping writer/read race, automatic timeout cleanup, cancellation, native Canvas generation policy, final physical reclamation or broader format/storage coverage is established. Both changed frames are produced by the owned receiving process while the sender waits for its acknowledgement, not by an asynchronous native preview stream. No Xcode windows opened, user processes terminated or system protections changed.
