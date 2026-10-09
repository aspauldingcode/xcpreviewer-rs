# Owned surface handoff across processes — 2026-10-09

A sealed sender/receiver experiment passes eight cases, each repeated with fresh peers: four surface shapes under both clean and abrupt sender exits. Every captured byte, including row padding, matches the independent Python expectation at three lifetime stages. See [checks and manifest anchors](../../research/evidence/surface-ipc-2026-10-09.json) and the [small native handoff golden](../../tools/re/fixtures/SurfaceIPCOracle/manifest.json).

This is a real Mach surface-right transfer between owned processes. It is not Apple's recovered XPC envelope or a canvas snapshot. The existing blank canvas and native instrumentation blocker remain unresolved; this campaign does not retry them.

## Handoff and lifetime

The receiver creates a randomly named temporary rendezvous, then forks and immediately executes the owned sender helper. The sender creates the surface after exec, so the result cannot come from an inherited surface allocation. The public [IOSurfaceCreateMachPort](https://developer.apple.com/documentation/iosurface/iosurfacecreatemachport(_:)) API produces a port holding a reference to the owned surface. Apple documents that this can pass a surface to another task without making it globally discoverable, and that the returned port must be deallocated. [IOSurfaceLookupFromMachPort](https://developer.apple.com/documentation/iosurface/iosurfacelookupfrommachport(_:)) creates the receiving reference without destroying that port.

The helper executes this fixed sequence:

1. Sender initializes the complete allocation and writes deterministic single-plane BGRA pixels with initialized row padding.
2. Sender transfers a Mach send right in a complex message. Receiver checks the kernel-provided audit PID against its spawned child, validates descriptor/metadata shape and looks up the surface.
3. Receiver checks initial bytes, XORs byte zero with `0x5a`, then deallocates the received surface port.
4. Sender checks the reply's audit PID, reads the receiver's mutation through its original surface and confirms the exact shared bytes.
5. Sender either releases its references and returns zero, or calls `_exit(23)` without normal cleanup. Receiver requires the corresponding actual wait status.
6. Receiver checks retained bytes after sender exit, XORs byte one with `0xa6`, checks again and releases its surface reference.
7. Receiver destroys the rendezvous receive right and requires bounded lookup to report unknown service before reporting success.

All four shapes (`1×1`, `3×2`, `17×3`, `33×7`) pass under both modes. Two repetitions produce 16 owned sender/receiver pairs. All lifecycle flags require actual booleans; the verifier also requires distinct recorded sender/receiver PIDs, matching exit mode/status, valid geometry and complete exact snapshots. Every helper reports successful rendezvous disappearance. There are zero helper failures in the final run.

The 3×2 golden has a 128-byte stride and 256 captured bytes. Its initial snapshot and post-sender-exit snapshot match the earlier local-reference native golden byte for byte, independently confirmed by system `cmp`. The final receiver snapshot differs from initial bytes at two prescribed offsets and eight bits. Byte equality proves these captures only; the finite corpus and independently predicted pattern define the supported behavior.

## Calibration failures and bounds

An inherited registered-port rendezvous attempt reported a send in the child while the parent timed out. The cause was not established. That manual route was abandoned; its diagnostics remain local.

The first sealed temporary-rendezvous run reached its handoff byte checks but treated explicit unregister as a required operation. The legacy bootstrap API rejected it with code 1101, causing all 16 helpers to fail and the experiment to remain inconclusive. That run stays sealed. The corrected helper destroys its receive right and polls its own unpredictable service name for disappearance; the final eight-case experiment supports its declared checks.

Bootstrap registration is deprecated. This helper is a local research control tied to the measured OS, and may be unavailable under another sandbox or OS version. It installs no persistent agent. Names contain a 128-bit random nonce; messages are accepted only from the audit-verified owned peer. No user Xcode, simulator or preview process is attached or terminated in this campaign.

Bounds: three-second Mach send/receive limits, twelve-second helper alarms, fifteen-second caller timeout and the controller's outer worker watchdog. On failure, the parent reaps or stops only its own child. Native logs, executable copies and snapshots remain in frozen-source sealed runs; publication contains small owned synthetic goldens and sanitized results.

## Acceptance and next experiments

All 67 automated tests pass. New checks reject changed padding, missing lifetime stages, same-process identities, integer attestations, wrong exit modes/status and corrupted golden bytes. The controller has 20 reviewed adapters and 19 MCP tools. Final artifact/frozen-source hashes verify against published manifest anchors; the scoped claim is indexed. The earlier cleanup failure remains inconclusive.

Established: owned CPU surface handoff, shared mutation, received-port release and receiver survival after the tested sender exits. Open: final-release reclamation, port/right leak counts, surface reuse, message ordering, concurrent release races, receiver-first exit, GPU completion/fences, multi-plane formats, revocation and actual canvas XPC ownership. Sender exit does not imply that a receiver's retained reference is revoked. Next discriminating work should test receiver-first exit and explicit reuse/completion identities before attempting attachment replay.
