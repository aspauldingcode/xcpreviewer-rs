# Owned two-queue event generation ordering

Two fresh owned Metal executions discriminate a completed command from a fresh frame. Reusing an already-signaled event value lets a reader finish with the previous generation while the next writer remains blocked. Waiting for the new generation's signal yields the new bytes. This adds a native R2/R3 oracle beyond the prior serial same-queue texture reuse; it does not recover Canvas synchronization or transfer an event between processes.

## Prediction and observations

Baseline: macOS 26.5.1 (25F80), Xcode 26.6 (17F113), arm64, Apple M1 unified memory. Two shared 16-KiB buffers, two distinct command queues, and one shared event retain their local resource tokens throughout each execution. The full buffers start with source `0xa5` and destination `0x5c`; six 256-byte rows each contain 44 active bytes.

The first reader is committed before the writer and waits for event 2. The writer waits for event 1, fills active source bytes with `0x22`, and signals event 2. Before CPU signal 1, a 20-ms reader completion wait times out, its callback count is zero, and event remains zero. Both pending samples are committed status 2, which does not prove hardware arrival at the wait instruction. After release, both commands complete exactly once and source/destination snapshots match the independent complete-allocation oracle.

The second writer waits for event 3 and will signal 4 after writing `0x77`. A deliberately stale reader instead waits for event 2. It completes exactly once while the second writer's callback count remains zero and event remains 2; its destination is exactly the old `0x22` frame. CPU signal 3 releases the writer; a reader waiting for 4 then returns exactly `0x77`. No CPU snapshot of a pending destination is used. No unsynchronized concurrent writer/read data race is introduced.

Fourteen complete allocation comparisons across two repetitions cover 229,376 bytes, including all row padding and allocation tails. Each command completion has a five-second bound; each subprocess has a 15-second deadline and the helper has a 20-second alarm. Both actual subprocess waits are zero with no stderr. Compilation also has a 15-second deadline. The exclusive controller lock covers source writes, compilation, and owned execution.

## Identity and verifier separation

Current REA MCP server `rea` / package `rea-agents` 6.2.0, started `2026-10-10T21:29:54.401Z`, independently inspects the owned arm64 Mach-O. Evidence `ev_37adbcc2d33a90568af17715572b5ef2476375982a7f62bbf38f3359ba853c63` binds its SHA-256 `e779349687d8e4bb3b0587af44d58ffbe5273301b73dbd58431bf2ea68d009c1` to the executed helper digest. Native-provider file/lipo/otool provenance is retained. This is static helper identity, not an independent observation of GPU execution. The native runtime observations come from the owned helper; the Python verifier independently predicts every byte and rejects six resealed wait, event, early writer, resource, stale-frame, and padding faults.

One REA call supplied an unsupported `path` argument to `inspect_macho` and was rejected before inspection. It is retained with acceptance false. Binding the owned target with `open_binary` and using `inspect_macho({})` resolved the API mistake; the session was closed. No failing native run or deadline extension occurred. Live server alignment remains unknown rather than an assertion of registration equivalence.

Evidence: `research/evidence/gpu-queue-order-2026-10-11`, manifest `0841c787c1afff6c0da6833cb5dd78dd5f82ed02c2669e948ae09a71109c615c`. Only owned source, sanitized buffer results, metadata and verifier are published; the compiled helper remains local. Reproduce by compiling `tools/re/gpu_queue_order.m` with `xcrun clang -Wall -Wextra -fobjc-arc -framework Foundation -framework Metal`, then execute it under the same deadlines and exclusive lock. `tools/re/tests/verify_gpu_queue_order.py` accepts only sealed evidence, exact waits and independently expected full bytes.

## Remaining acceptance

These finite public-Metal controls demonstrate generation-specific ordering across two owned queues on one device. They do not establish cross-process event transport, IOSurface/Mach release accounting, physical reclamation, automatic timeout cleanup, cancellation, broader formats/storage modes, native Canvas ordering, or portable GPU synchronization. R1/R2/R3 and both milestones remain open. The approved private Xcode bridge remains offline; no restart or Xcode workspace was opened.

Next: use this counterexample to verify a scoped consumer generation fence where demanded, or recover a separately observed native completion boundary. Do not repeat unchanged serial reuse or attempt private capture until its restoration prerequisite changes.
