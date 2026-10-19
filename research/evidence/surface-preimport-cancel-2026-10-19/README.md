# Owned IOSurface cancellation after dequeue, before import

This four-case owned CPU experiment measures a previously unmeasured R1 cancellation boundary. COPY_SEND and MOVE_SEND each have a full-import control and a deliberate cancellation branch after an audited full message dequeue but before IOSurfaceLookupFromMachPort. Sender explicitly releases its original local CF and Mach handles before audited stage6 authorization.

All four children report queue depth 1 to 0 and one received send reference before mach_msg_destroy. Cancellation performs no CF lookup/acquisition/release; the received resource and both local endpoints then query KERN_INVALID_NAME (15). Positive controls retain a CF alias across Mach-right destruction, read the allocation, mutate byte0 with XOR0x5a and release the alias. Parent receives audited stage7, performs actual waitpid with exit0, observes peer dead names and removes its own endpoints and random rendezvous.

The independent consumer compares ten complete 16,384-byte allocations (163,840 bytes), including 5,400 row-padding bytes and 152,320 unused tail bytes, to a separately calculated pattern and mutation. The cancel branches have sender snapshots only; no receiver pixels are fabricated. Synthetic fault tests are schema/consumer controls built from a historical fixture, not additional native executions.

One compile, one output control and one four-case fixture completed before the fixed 08:28 UTC deadline. No retry or Xcode workspace was opened. The guard reports zero remaining observed processes. The children are brief and were not observed in every periodic ancestry sample; audited acknowledgments and actual waitpid are separate source-bound child-completion evidence. Unseen process escapes remain outside observer coverage.

This falsifies the scoped claim that a dequeued IOSurface descriptor must be imported to remove its received local Mach name, within these owned controls. It does not establish asynchronous cancellation behavior, all internal/global references, physical reclamation, GPU behavior, cross-case identity from recycled numeric IDs, general reliability, or native Canvas transport/completion. R1, R2, capture and both milestones remain open. Prior UI registry quarantine and the multi-call native UI cleanup block remain unchanged.

Replay: `python3 -B verify-frozen.py` and `python3 -O -B verify-frozen.py`. No executable is published or launched by replay. Native execution adapters are historical transcriptions with an expired deadline and original temporary paths, not replay entrypoints.

Next: skip this completed dequeue-before-import branch. Select an independently discriminating post-import/pre-ack failure or completion boundary only after coverage review, retaining local-reference versus physical-reclamation distinctions. Native UI execution requires a changed, reviewed bounded cleanup strategy; no repeat of the expired window experiment.
