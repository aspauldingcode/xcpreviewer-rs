# Receiving-process GPU readback from imported IOSurface

An owned audited receiver now creates a Metal texture from its imported IOSurface and completes a texture-to-buffer blit. Independent exact bytes verify the GPU readback before the existing CPU mutation and clean/abrupt exit controls. This advances from a CPU-only peer to Metal work in both producer and receiver processes.

Baseline: Xcode 26.6 (17F113), macOS 26.5.1 (25F80), arm64, Apple M1, shared BGRA8Unorm. The previous GPU Mach handoff seal was verified against its committed anchor before extension.

## Ordered execution and predictions

Producer GPU clear completes before audited Mach transfer. The receiving process imports the same surface ID, constructs an IOSurface-backed shared texture and a separate 16,384-byte shared Metal destination buffer, and initializes that entire destination to `0x5c`. Its chosen destination row stride rounds width*4 up to 256 bytes; this is an owned layout choice, not a recovered native Canvas stride rule.

The peer encodes a texture-to-buffer blit for exactly the selected width/height, registers a completion handler and commits. A semaphore deadline of five seconds, one observed callback, completed command/handler status and no error gate the CPU destination snapshot. The existing twelve-second helper alarm, fifteen-second subprocess deadline and controller budget still bound the whole experiment.

The independent comparator predicts opaque red/blue BGRA active pixels with `0x5c` destination row padding and allocation tail. Source comparisons continue to require `0xa5` padding/tail and the expected CPU mutations. Consumer sidecar PID and surface ID must match the audited peer record. Source and destination storage modes, layout, completion types/counts/status and error flags are checked explicitly.

Four geometries, two exit modes and two repetitions give 16 owned executions per campaign. Each peer readback campaign compares 128 whole allocations totaling 2,097,152 bytes, including producer initialization/render, destination initialization/readback, imported CPU snapshot, post-exit/mutation and port-only snapshots. Both consumer campaigns pass exactly; the original producer-only GPU handoff campaign passes after the shared adapter changes.

## Fault controls and remaining scope

Added synthetic rejection controls for wrong consumer PID/surface ID, callback types/status, error flag, source storage mode, missing readback, wrong destination stride/allocation extent, active bytes, row padding and allocation tail. Consumer mode requires the reviewed producer and receiver-first configuration. The suite passes 140 tests. Three new seals are verified against anchors in [sanitized evidence](../../research/evidence/gpu-peer-readback-2026-10-09.json).

R1/R3 remain open. This is ordered producer completion followed by peer Metal readback; it does not measure unsynchronized overlap, native Apple fence/event behavior, timeout/cancellation recovery, other formats/storage modes or final reclamation. API calls/status/bytes are measured, not hardware instruction execution traces, zero-copy properties or GPU performance. No actual Canvas envelope is captured. No Xcode windows opened, user processes terminated or system protection changed.

Apple documents the [texture-to-buffer blit operation](https://developer.apple.com/documentation/metal/mtlblitcommandencoder/copy%28from%3Asourceslice%3Asourcelevel%3Asourceorigin%3Asourcesize%3Ato%3Adestinationoffset%3Adestinationbytesperrow%3Adestinationbytesperimage%3A%29?language=objc); the sealed measurements support only this owned baseline and explicit completion ordering.
