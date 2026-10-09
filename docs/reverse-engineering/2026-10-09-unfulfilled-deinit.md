# Unfulfilled-state destruction diagnostics

Four bounded static probes follow FulfillOnceState.deinit and its deallocating destructor, then inspect Foundation state metadata. The image remains pinned to prior continuation/default-policy anchors.

The destructor obtains a state snapshot through SynchronousAccessProviding.peek and queries its multi-payload enum case. Case 1 destroys the snapshot and skips diagnostic construction. The other branch destroys its copied payload, constructs an Unfulfilled error and calls the previously reviewed failure policy before common reference cleanup. On normal return, shared cleanup releases stored references; the deallocating destructor calls this body and tail-calls Swift class-instance deallocation. A non-returning diagnostic policy can prevent reaching that cleanup. This is not Mach/IOSurface reclamation evidence.

Static nominal metadata declares the nested State enum cases `waiting` and `fulfilled`. The target descriptor and names are verified separately from destructor names. Field order alone is not assigned runtime case tags. Symbolic payload types remain unresolved, and seven broader metadata parse errors are retained. There is no complete private Swift ABI recovery.

Two finite control modes automate the observed boundaries. deinit_control requires the exact snapshot/case-query sequence, case-1 skip, Unfulfilled allocation/failure-policy sites and normal cleanup/return. Mutated discriminator, branch, skip target, allocation, policy, snapshot and return evidence fail. state_control requires a unique nested State descriptor of enum kind with the two declared names; missing/duplicate descriptors, changed kinds, counts, parents and case order fail. Neither checker is a general control-flow interpreter or native destructor execution test.

Initial metadata acceptance mistakenly checked an absent result field; its sealed inconclusive run is retained. The corrected experiment checks the target and explicitly retains seven global errors. Four seals verify and all 129 tests pass. No Xcode windows opened, private Swift ABI calls or process attachment used. [Sanitized evidence and anchors](../../research/evidence/unfulfilled-deinit-2026-10-09.json) preserve scope and the failed check.

An abandoned continuation may enter a diagnostic path, but this does not establish an automatic error callback, reply timeout or resource revocation. Safe native runtime observation, actual caller policy, case mapping, cancellation races and correlated transport remain required. R2 and both milestones remain open.
