# Queued IOSurface attachment discarded before import

Four owned peer executions measure a previously untested failure boundary: a surface descriptor is successfully queued, then the receiver destroys its receive right without receiving or importing the attachment. COPY_SEND leaves one sender send reference; MOVE_SEND removes the original sender name. Retained sender CF storage remains readable after receiver endpoint destruction and exit, then a replacement Mach port alone preserves exact mutated storage after the original CF owner drops. Completion remains rejected.

## Why this control differs

Earlier closed-endpoint controls reject transfer before queueing; post-import controls observe an imported resource. Here the owned child exposes separate attachment and control inboxes. The parent successfully sends one IOSurface descriptor into the attachment inbox, then an audited control message authorizes its destruction. The child receives only from the control inbox, measures attachment inbox message count exactly 1 using MACH_PORT_RECEIVE_STATUS, and removes that receive right without calling receive or IOSurfaceLookupFromMachPort for the attachment. The child also removes its control receive right, reports the measured queued count through the parent's inbox, releases its parent send name, and exits 45. Parent waits for that actual exit.

Both parent observations (ready and discard acknowledgement) verify the child's audit PID; the child's control observation verifies the parent's audit PID. Child mode additionally requires getppid equality. One random temporary bootstrap rendezvous is scoped to each helper. Unknown/user processes are never selected; failure cleanup targets only that helper's forked child. No Xcode workspace is opened.

The two modes differ only in descriptor disposition: COPY_SEND versus MOVE_SEND. After successful send, COPY has one measured sender send reference; MOVE has an invalid original name. After peer exit both exported endpoint names are measured dead names and later explicitly removed. In COPY mode, dropping the remaining resource send reference removes that local name. A newly exported replacement surface port has one send reference; after original CF drop, lookup from that port gives the same surface ID and exact mutated full allocation. Its final send name is removed explicitly. Rendezvous lookup reports removal. Numeric Mach names and surface IDs are local observations, not durable/global identities.

This accounts for the selected local endpoints and reference paths. It does not count hidden global/kernel references or observe physical reclamation of the queued attachment. The receiver never imports it; no imported right count or receiver pixels are invented. CF retention intentionally prevents a final storage reclamation claim. Discard acknowledgement is an owned control fact, not preview completion.

## Bytes and provenance

Native environment: macOS 26.5.1 (25F80), Xcode 26.6 (17F113), arm64. Both modes use an 11×6 single-plane BGRA surface, seed 33, measured stride 128 and allocation 16,384 bytes. The independent Python reader predicts RGB channels with `(seed + x*17 + y*31 + channel*53) & 255`, alpha 255, and all row padding/allocation tail as `0xa5`. It checks before-send and post-discard snapshots, then the replacement-port-only snapshot with byte 0 XOR `0x5a`. Twelve complete allocations total 196,608 independently expected bytes, equal across modes and repetitions. Row padding is 84 bytes per row; the last allocation byte is included.

Four native helper invocations exit zero with actual child exit45/signal0. Compile and helper subprocess deadlines are 15 seconds; helper alarm is 12 seconds; individual sends/receives have three-second caps. Compilation retains three bootstrap_register deprecation warnings from the scoped existing mechanism; they are not suppressed or converted to execution failures. No retry or deadline extension was needed.

REA package/server 6.2.0 binds the executed owned arm64 artifact SHA-256 `704d37b7a80d082e64e310c4d5d20fb9e25f7d2e762a2230a5185dac49360f72`, evidence `ev_a8e335ae259db75d1bb01bcb8938d6386cd61dbdcf6fc31743decd37ca47f7e3`. Inline native utility provenance and compact live server identity are retained; the owned target is closed. Static artifact inspection does not claim to observe the Mach handoff at runtime. The frozen included surface primitive source is checked against the current helper, as is the new control source. Executables remain local.

Seven resealed faults change queued count, MOVE sender references, completion acceptance, peer PID, actual helper exit, padding byte44 and allocation tail byte16383. Independent verification must reject each despite replacement valid hashes. Candidate checks also verify the prior submission/destruction callback evidence, parent seal `d8500f8f4038a772748b22e68233a7316640fc3c079e1e5e1c14c02b3aa0c9a1`.

Evidence: `research/evidence/surface-queued-drop-2026-10-11`; manifest `dd1acfa45665be4314909cefbea7b8f3b02228abeaee84baad73a800686ef7a9`. Reproduce by compiling `tools/re/surface_queued_drop.c` with `xcrun clang -std=c11 -Wall -Wextra -framework CoreFoundation -framework IOSurface -lbsm`, then run `copy` or `move` with a new owned output directory under the exclusive controller lock and retained deadlines.

## Remaining acceptance

This is a finite CPU IOSurface/Mach failure control. It does not recover actual Canvas/XPC envelopes, GPU failure/cancellation, simultaneous release races, arbitrary name recycling, multi-plane/discrete storage or final physical reclamation. R1/R2 and both milestones stay open. The private approved Xcode bridge remains offline; restoration remains a separate prerequisite from available REA and no automatic restart occurs.

Do not repeat unchanged queued-drop controls. Next choose a required failure boundary with a different ownership transition, or a demanded portable product contract. Preserve COPY/MOVE disposition distinctions and reject completion claims merely inferred from transport/control acknowledgements.
