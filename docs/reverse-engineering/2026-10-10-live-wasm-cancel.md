# Persistent WASM close and quiescence

The owned cancellation control falsified the initial host's close contract:
`close()` returned while a proposal promise was still unsettled, and that
proposal subsequently failed only at its own deadline. Closing the active
worker did not close the separate candidate worker. The retained before-fix
receipt records this failure; close elapsed time is diagnostic, not acceptance.

The host now retains the candidate handle and an operation-settlement promise.
Close marks the host terminal, clears its published snapshot, terminates active
and candidate workers, and waits for the in-flight operation's cleanup. Worker
exit events maintain an explicit live-worker inventory. Constructor failures
also enter the operation cleanup path. Live verification captures its active
instance before awaiting and checks terminal state before returning, preventing
a null-reference race or success after close.

Actual V8 controls now cover an infinite-loop proposal, an empty-host valid
proposal, an active-host valid proposal, and an active live-read interrupted by
close. Repeated simultaneous closes are idempotent. Each final receipt has zero
live workers, no busy operation, a terminal host, an empty snapshot and no late
revision. Competing proposals reject while last-good snapshot bytes remain
unchanged. The earlier two-revision/six-fault controls still pass and now verify
one worker after replacement or candidate rejection and zero after final close.
Both Python tests impose fifteen-second subprocess limits.

Evidence: `research/evidence/live-wasm-cancel-2026-10-10/manifest.json`. This is
owned Node worker lifecycle/reconstruction policy, not evidence of native Canvas
resource accounting or release acknowledgment. No Xcode workspace was opened.
Native UI availability and private bridge restoration remain prerequisites;
scientific review, graph binding and both milestones remain open. Next: prepare
source-built candidates and run the complete independently anchored native extent
corpus through the persistent host, then review and bind the bounded adapter.
