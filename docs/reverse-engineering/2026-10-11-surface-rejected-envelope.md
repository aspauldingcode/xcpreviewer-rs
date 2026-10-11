# Rejected envelope with coalesced IOSurface descriptor rights

Four owned native peer controls receive an intentionally invalid application envelope carrying two copies of one IOSurface send right. Both received descriptors coalesce to one task-local name with two send references. Whole-message destruction removes that name. Explicitly releasing one descriptor and clearing its name leaves one reference, then message destruction removes the name. Sender retained storage remains exact after rejected-peer cleanup/exit; completion is never accepted.

## Changed ownership boundary

The parent queued-before-import control, seal `dd1acfa45665be4314909cefbea7b8f3b02228abeaee84baad73a800686ef7a9`, destroys an attachment inbox without receiving its message. Here the owned receiver actually receives the complex message, so descriptor rights enter the receiver's namespace before application rejection. This measures receiver cleanup after delivery rather than queue destruction before delivery.

The owned parent sends one two-descriptor envelope with COPY_SEND for both ports. Its deliberately invalid application magic is `0xdeadbeef`, different from the fixture's valid MAGIC. A separate audited control inbox orders reception after queue count1 is measured. The receiver checks parent audit PID, message extent, complex bit, descriptor count2, both descriptor types/send dispositions and the expected invalid fixture magic. It never calls IOSurfaceLookupFromMachPort for either descriptor. This is a known-invalid controlled fixture, not a production parser or proof of arbitrary malformed-envelope validation.

Both descriptors name the same task-local port and a direct send-reference query reports 2. In mode `all`, mach_msg_destroy consumes both descriptors and the name becomes invalid. In mode `partial`, explicit mach_port_deallocate reduces references to1, then the consumed first descriptor name is set to MACH_PORT_NULL before mach_msg_destroy. That prevents treating an already consumed reference as still owned by the message; destruction consumes the remaining reference and the coalesced name becomes invalid. This control does not intentionally execute the unsafe double-release alternative.

The receiver removes its attachment/control receive rights, reports pre-destruction reference count2/1 to the audited parent, removes its parent send name, then exits46. Parent verifies actual exit46/signal0 and both exported inbox names as dead names. Sender COPY send references remain1 after send; dropping the remaining send reference later removes its local name. Parent still owns CF storage through rejection/exit, verifies it, mutates byte0 with XOR0x5a, exports a replacement port with one send reference, drops original CF, imports only in the parent and verifies the same surface ID and exact mutated storage. Replacement and endpoint names plus temporary bootstrap rendezvous are explicitly removed. Names/IDs are local observations, not durable identities or frame generations.

Audited parent ready/rejection acknowledgements bind child PID; the child's control and attachment messages bind parent PID. Child mode also requires getppid equality. Only a helper-owned forked child is eligible for bounded failure cleanup. No unrelated process, Xcode workspace or simulator is touched.

## Independent bytes, faults and provenance

Native baseline: macOS26.5.1 (25F80), Xcode26.6 (17F113), arm64. Each mode repeats twice with fresh owned peers. Both use 11×6 single-plane BGRA, seed33, stride128, allocation16,384. Independent Python predicts every RGB/alpha pixel, all84 padding bytes per row and allocation tail as0xa5, then byte0 XOR0x5a for the port-only snapshot. Twelve complete allocation comparisons total196,608 bytes. All stages/modes/repetitions agree with independent expectations.

All four actual native waits are0 and peer exits46. Compile/native subprocess deadlines stay15 seconds; helper alarm12 seconds; send/receive caps3 seconds. The existing bootstrap_register mechanism emits three retained deprecation warnings; no retry or deadline increase was needed.

REA package/server6.2.0 binds executed owned arm64 artifact SHA-256 `73da0e36be15c702e912c7e171c1e660d32eef61c9cf2db8e792f30600010359`, evidence `ev_59882a88b1372885f7505c58d14c00cac36064d66f58e5539c064a1f93a5ba98`. Compact server identity and native utility provenance are retained and the owned target closes. Artifact inspection is static; owned subprocess outputs supply the runtime measurements. Executables remain local. Frozen new and included primitive sources must match current sources.

Seven independently resealed faults change queued count, partial-path reference count, completion acceptance, peer PID, actual helper exit, padding byte44 and tail byte16383. Each must fail despite a correct replacement file hash. Isolated candidate checks also verify the parent queued-drop evidence. These are finite control predicates, not general hostile-input conformance.

Evidence: `research/evidence/surface-rejected-envelope-2026-10-11`; manifest `1b82bc521056230d812b4d44f7cdfa4430f11e239bb183d681cb22cae5df7bda`. Compile `tools/re/surface_rejected_envelope.c` with `xcrun clang -std=c11 -Wall -Wextra -framework CoreFoundation -framework IOSurface -lbsm`; run `all` or `partial` with a fresh owned output directory under the exclusive controller lock and retained deadlines.

## Acceptance limits and next work

This supports local right accounting for an owned rejected envelope and explicitly transferred descriptor ownership during partial cleanup. It does not measure global/kernel holders, final physical reclamation, GPU cancellation/failure, arbitrary malformed parsers, simultaneous release/name recycling or actual Canvas/XPC transport. Retained sender CF storage intentionally excludes final release. R1/R2 and both milestones stay open.

The approved private Xcode bridge remains offline, separate from available REA; no restart or workspace opened. Do not repeat unchanged queue/rejected-envelope controls. Select a required distinct ownership/failure boundary or demanded portable product contract. Keep message-owned references and manually consumed references separate in any adapter; a rejection acknowledgement is not preview completion.
