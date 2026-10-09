# Owned GPU surface completion and retained CPU access

A public Metal/IOSurface control now verifies GPU-produced BGRA bytes after command completion on Apple M1. This fills a previously missing owned GPU-to-CPU observation boundary. It is separate from Xcode Canvas and interprocess GPU ownership.

Baseline: Xcode 26.6 (17F113), macOS 26.5.1 (25F80), arm64, Apple M1 unified memory. The helper uses an IOSurface-backed `BGRA8Unorm` shared texture and render-pass clear/store operations; no private framework ABI or native process attachment is used.

## Prediction and observed results

Initialize the entire IOSurface allocation to `0xa5`. Render opaque red, identical red, then opaque blue into the same texture. An independent Python comparator predicts literal BGRA bytes (`00 00 ff ff` red and `ff 00 00 ff` blue) and leaves every row-padding and allocation-tail byte as `0xa5`.

For each render, register a completion handler before commit, wait at most five seconds for its semaphore, then require one observed handler call, completed status from both handler and command, and no error. Only then lock/read the IOSurface. The helper has a twelve-second alarm and the adapter a fifteen-second subprocess deadline; compilation and the controller also have bounded deadlines.

Four geometries (`1x1`, `3x2`, `17x3`, `33x7`) run twice in separate helpers. All observed allocations are 16,384 bytes. The corrected initial control verifies 32 whole-allocation comparisons (524,288 bytes), including initialization and three GPU results. Each red/red repeat and cross-helper repeat matches exactly.

A dependent control drains each command's autorelease scope and drops explicit texture/queue references after the blue completion. The retained CF IOSurface remains readable and unchanged. It verifies 40 whole-allocation comparisons (655,360 bytes), including eight post-drop snapshots. This is retained-access evidence; internal driver holders and physical reclamation remain unknown.

## Harness failure and verification

The first sealed run was inconclusive: native `error_absent` was boxed as integer `1`, which the strict Boolean checker correctly rejected. Changed serialization uses `numberWithBool`; neither expected pixels nor padding requirements were relaxed. The initial seal and outputs remain retained.

Three new runs are sealed and checked against the anchors in [sanitized evidence](../../research/evidence/gpu-surface-completion-2026-10-09.json). The suite passes 135 tests. Synthetic faults corrupt active pixels, row padding, the second row, allocation tail, final color, post-drop color, completion count/status, identity, storage mode, Boolean types and absent evidence. All reject.

R1/R3 remain open: no GPU Mach/XPC handoff, actual Canvas synchronization, early-read hazard, timeout/cancellation recovery, multi-plane/managed/discrete-GPU coverage, or final resource reclamation is established. No Xcode windows were opened and no system protection changed.

## API references

Apple documents [IOSurface-backed Metal textures](https://developer.apple.com/documentation/metal/mtldevice/maketexture(descriptor:iosurface:plane:)), [completion handlers called after GPU execution](https://developer.apple.com/documentation/metal/mtlcommandbuffer/addcompletedhandler(_:)), and the requirement to finish work before cross-processor access to [shared storage](https://developer.apple.com/documentation/metal/mtlstoragemode/shared). Those API descriptions motivate the control; the sealed measurements establish the reported bytes only for this owned baseline.
