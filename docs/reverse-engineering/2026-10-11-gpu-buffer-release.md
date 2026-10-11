# Owned Metal buffer retention and ARC object release

Dropping the CPU's strong buffer variable does not release the buffer object while an encoded command retains its resources. Two owned native executions observe that retention both before an uncommitted command and across a committed event timeout. After completion (where applicable), command disposal and autorelease-pool drain, all four weak buffer and command observations become nil. This advances the public-Metal object lifetime oracle for R1/R2 without claiming physical memory reclamation or actual Canvas release accounting.

## Independent controls

Baseline: macOS 26.5.1 (25F80), Xcode 26.6 (17F113), arm64, Apple M1 unified memory. Each mode creates a shared 16-KiB buffer initialized entirely to `0x5c`. A command with measured `retainedReferences=true` encodes wait-for-event-1 and fills 44 active bytes in each of six 256-byte rows with `0x77`. The CPU strong buffer variable and encoder variable are explicitly dropped. Weak buffer observations retain the original local pointer token.

The encoded-uncommitted control remains status 0 with zero callbacks and event 0; its full buffer stays unchanged. The committed control observes a 20-ms completion timeout, no callback, event 0, and a live weak buffer after the CPU owner dropped. Pending status is 2 in both runs; this does not locate hardware execution at the wait instruction. The fixture explicitly signals event 1 before assessing the negative control. Within a five-second bound the command completes exactly once, status 4 with no error. Only then is its full buffer copied; active bytes become `0x77` while all padding and tail stay `0x5c`.

Both modes keep the buffer object alive until the final in-pool snapshot. Clearing the command variable and draining the pool, which also ends queue/event/temporary object lifetimes, yields weak command=nil and buffer=nil. The control does not isolate a sole internal owner. ARC weak loads can temporarily retain an object; the pool boundary is part of the measured fixture. Numeric pointer tokens happened to repeat between the two successive modes after weak nil, so they must not be used as durable resource identity.

Eight independent whole-allocation comparisons across the two repetitions cover 131,072 bytes. Both actual subprocess waits are zero with no stderr. Compilation and each subprocess have fixed 15-second deadlines; the helper has a 20-second alarm. The exclusive controller lock covers all writers and owned execution. There is no CPU data snapshot while the committed command is pending and no unsynchronized writer/read race.

## Provenance and falsification

Current REA MCP confirms server `rea` and package `rea-agents` 6.2.0, started `2026-10-10T21:29:54.401Z`. It binds the executed owned arm64 Mach-O SHA-256 `46066d393225b45bccbca6c0f06687805f3c11afd951b59c0e5994d75af15c86` through native inspection evidence `ev_fc0d494262cf300b2bc4aeb3fd6e8ee756f3ac6b6d0457396bea40dc02ffe61e`. Native utility provenance is retained and the target session is closed. Static helper identity is separate from the helper's runtime observations; registration alignment remains unknown.

The Python verifier independently predicts all full buffer bytes and rejects six resealed faults: actual wait failure, missing pending weak owner, post-pool weak liveness, early callback, pointer mismatch and padding byte 44 corruption. It also requires the current helper source to match the frozen executed source. No unplanned native failure or deadline extension occurred.

Evidence: `research/evidence/gpu-buffer-release-2026-10-11`; manifest `9cb67c04646592908039c9a3f0f04e62fac07a56af58f8ab196f92d20affa4ea`. Parent two-queue seal `0841c787c1afff6c0da6833cb5dd78dd5f82ed02c2669e948ae09a71109c615c` was verified before extension. Published artifacts are owned source, sanitized observations, metadata and verifier; the executable remains local. Reproduce by compiling `tools/re/gpu_buffer_release.m` with `xcrun clang -Wall -Wextra -fobjc-arc -framework Foundation -framework Metal`, then run with the same lock/deadlines. The verifier accepts sealed results rather than success-shaped stdout alone.

Weak nil observes Objective-C object lifetime, not allocation reuse, residency, Metal driver/global holders, IOSurface/Mach right release or final physical memory reclamation. Explicit event recovery is not cancellation or automatic timeout cleanup. Actual Canvas ownership/transport, R1/R2 acceptance and both milestones remain open. No Xcode workspace opened; the approved private bridge remains offline with restoration prerequisite unchanged and no restart attempted.

Next: quantify a demanded scoped owner ledger using these independent native observations, or investigate a separately observable native failure/release boundary. Do not repeat these unchanged weak-reference controls or promote weak nil to kernel reclamation.
