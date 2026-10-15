# Synchronous observation callback contract

Observation callbacks returning promises or thenables previously escaped the synchronous cancellation path. Twelve frozen source controls retain before/after results: resolved, rejected, pending and custom thenable results now reject with an explicit synchronous-contract error; throwing then getters retain their original error, and plain synchronous return values remain accepted. The rejected promise is consumed to prevent unhandled rejection. Before behavior is captured with a controlled source-only unhandled-rejection listener; unsafe before native jobs were not launched.

Two owned native controls return resolved and rejected promises after observing a root and its ready detached child. Both request private abort, retain root completion 43 and actual child wait 42, report drained with zero remaining observed processes, and preserve all 16 controlled payload bytes against independent expectations. No emergency cleanup was required. Source and native acquisition budgets each remain two of two consumed.

The independent sealed reader checks source hashes, full raw payloads, receipts, identities, cancellation and outcomes. Twelve resealed faults must fail verification. Current primitive-error handling receives twelve fresh source regressions; raw output accounting receives 24 fresh controls. Historical native evidence stays frozen.

This rejects unsupported asynchronous callback results; it does not await callbacks or add asynchronous callback support. Job deadlines and owned drain semantics are unchanged. Evidence qualifies the owned observer adapter, not native Canvas protocol, physical IOSurface reclamation, arbitrary noncooperative JavaScript or unseen processes. The private Xcode bridge remains absent; REA availability is separate. Both milestones and issues #15, #19, #22 and #25 remain open.

Evidence: `research/evidence/thenable-callback-2026-10-14`; manifest SHA-256 `d7ea916d9d6d23b371cf5425f0b76665b09fb70c6aeb6a555368442f4b31ac3b`. Next work: choose an independent eligible native or portable experiment; do not repeat these completed callback controls.
