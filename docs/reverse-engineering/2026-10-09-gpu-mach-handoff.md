# GPU-produced IOSurface Mach handoff and receiver exit

The owned Metal completion control now feeds a real audited Mach surface transfer. A CPU peer imports completed GPU-produced BGRA storage, mutates it, and exits; the producer retains exact access and accounts for its local send rights. This recovers an owned interprocess GPU-produced resource boundary, not Xcode Canvas's private synchronization protocol.

Baseline: Xcode 26.6 (17F113), macOS 26.5.1 (25F80), arm64, Apple M1 unified memory. Prior GPU completion seals were verified against their published anchors before extending the control.

## Construction and independent checks

The GPU variant initializes the entire allocation to `0xa5` without CPU-writing the expected pixels. Public Metal render-pass clear/store produces opaque red for seeds below 128 and blue otherwise. One bounded completion handler, completed command/handler status, and no command error are required before a full producer snapshot and before Mach-right creation/transfer. Producer sidecar metadata includes its PID, surface ID, dimensions, stride, allocation extent and completion observations.

The existing receiver-first peer control supplies random temporary rendezvous, audit-token PID checks, real IOSurface Mach send-right transfer, surface ID/geometry verification, deterministic CPU mutations and actual wait-status checks. GPU builds use full allocation snapshots, capped at 65,536 bytes; CPU builds preserve their prior stride-by-height comparison extent. The receiver exits either after explicit port/CF release or abruptly with exit 23 and live imports. The producer observes the exact selected exit status.

Each case checks sender send refs 1 before transfer, after COPY_SEND and after peer exit, then zero/no-right after final explicit drop. After peer exit, the producer mutates one byte, drops its original CF reference, imports using its retained Mach right, and checks the same allocation again. This proves retained access and local rights cleanup, not final physical reclamation.

Four geometries run in clean/abrupt receiver modes, each twice: 16 executions per GPU campaign. Independent Python literal BGRA predictions and separate mutation expectations compare producer initialization/render plus imported/after-exit/after-owner-mutation/port-only snapshots. All observed allocations are 16,384 bytes. Each GPU run performs 96 whole-allocation comparisons totaling 1,572,864 bytes, including every active pixel, row-padding byte and allocation-tail byte. Both colors and repeat controls pass.

## Falsification and regression checks

Added strict GPU producer checks bound to the peer record and completion result. Synthetic faults alter producer PID/surface identity, callback count/type/status, error Boolean, allocation extent, actual peer exit, audit flag, final right count, missing payloads, active bytes, row padding and allocation tail. Unsupported sender-first GPU configuration is rejected before execution. The original CPU sender-first and receiver-first native campaigns both pass after the shared helper changes. The full suite passes 138 tests.

Four new runs are sealed and verified against anchors in [sanitized evidence](../../research/evidence/gpu-mach-handoff-2026-10-09.json): two GPU campaigns and two CPU regressions. Raw helper artifacts remain local. Compiler deprecation diagnostics for the existing bootstrap rendezvous are retained; operation is qualified only on the pinned baseline.

R1/R3 remain open. The peer consumes with CPU access after producer GPU completion; it does not execute GPU work in a second process or exercise unsynchronized early reads, GPU timeout recovery, concurrent cancellation, managed/discrete GPU memory or multiple planes. No actual Canvas envelope or private completion policy is recovered. No Xcode windows opened, user processes terminated, system protections changed, or private Swift ABI constructed.
