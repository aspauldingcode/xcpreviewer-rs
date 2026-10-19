# Owned post-import acknowledgment timeout

This research isolates completion notification from explicit resource release in two MOVE_SEND owned CPU IOSurface cases. Both release the sender's original local CF/Mach handles before audited stage6, import the receiver alias, destroy its received Mach right (local name query15), read/mutate the allocation and release its CF alias before sending audited stage8. Parent stage9 authorizes the completion decision.

The timely control closes receiver endpoints, writes the receiver record and sends stage7. The withheld case sends audited stage10 and blocks on stage11, so stage7 cannot yet be sent. Parent verifies an empty completion queue, performs a 50ms requested receive and observes MACH_RCV_TIMED_OUT (0x10004003 /268451843), verifies the queue remains empty, then authorizes stage11. Receiver closes endpoints, writes its record and sends late stage7. Parent verifies the audited completion and actual waitpid/exit0 before removing peer dead names and its random rendezvous.

Both cases pass. Thus a completion receive timeout can coexist with already released explicit receiver resource handles; timeout is not a completion acknowledgment, and later acknowledgment/child exit require separate evidence. This does not show that timeout causes cleanup: CF/Mach release deliberately precedes the timeout. Stage8/10 causal ordering is source-bound through audited peer messages, not an observation of private Canvas protocol or all kernel references.

Independent admission compares eight complete16,384-byte allocations (131,072bytes), including4,320 row-padding and121,856 unused-tail bytes, against a separately calculated pattern and byte0 XOR0x5a mutation. Six synthetic normal/optimized methods test parent/child semantics, pixel/padding/tail corruption, prerequisite dispatch suppression and fixture phase/source binding. Synthetic records are derived from historical owned evidence and are explicitly modeled controls, not native executions.

One compile, one output control and one fixture completed before the unchanged08:43UTC deadline; no retries or Xcode sessions. REA6.2.0 arm64 digest matches compile/fixture receipts; no executable is published. Observed drain reports zero remaining observed processes. Some short-lived children can be missed by periodic samples; source-bound audited acknowledgments plus actual waits separately support child completion. Unseen escapes remain excluded.

Run `python3 -B verify-frozen.py` or `python3 -O -B verify-frozen.py` for offline evidence replay. Historical execution adapters retain original temporary paths and expired fixed gates; replay never launches native code.

No asynchronous Canvas cancellation/completion, automatic timeout cleanup, physical reclamation, global/internal reference accounting, GPU behavior, general reliability or cross-case identity from recycled numeric IDs is qualified. R1/R2/native capture and both milestones remain open. Previous registry quarantine and the multi-call native UI cleanup block remain unchanged.

Next: skip this completed release-before-missing-ack boundary. Audit resource-held versus notification-held timeout coverage and R2 reuse/generation/completion evidence before selecting another discriminator. Any native UI execution requires a changed, reviewed bounded cleanup strategy; do not repeat the expired workspace experiment.
