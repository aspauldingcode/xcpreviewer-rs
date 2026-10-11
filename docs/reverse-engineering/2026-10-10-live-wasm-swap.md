# Owned persistent WASM instance/frame swap

The graph selected `primary-live-wasm-swap`, which requires a reviewed execution
binding. A first implementation now prepares a proposed module in a separate
bounded worker, validates the fixed import-free primary-layer ABI, renders and
checks the complete allocation, and commits one active instance/frame reference.
The prior worker remains live until successful publication and is terminated
after replacement. Snapshot readers receive copies. One proposal or live-read
verification owns the host at a time; closed hosts reject proposals. Each
candidate has an independent deadline, so a trapping or infinitely looping WASM
proposal does not destroy the retained worker or frame.

Two pinned modules and complete allocations were copied from the independently
sealed source-frame CLI run `20261010T215404Z-primary-source-frame-cli-8a8fd3bc`.
The trusted outer manifest anchor is
`9dba73bc8a5098d92441a4bd5e34ada36548f2cbb51387ba2844b6d008cdd4ac`.
Both 16384-byte fixture allocations also match the independent primary-source
prediction, including padding and unused tail. This wake introduces no new
native callback capture; it reuses measured source-derived V8 frames.

Actual Node 24.19.0/V8 13.6.233.17 on macOS ARM64 accepts two revisions and gives
them distinct instance tokens. Six failed proposals cover malformed modules,
an owned unreachable trap, an owned infinite-loop timeout, and independently
flipped expected pixel, row-padding and unused-tail bytes. Every failed proposal
retains the exact prior revision/token/module hash and all 16384 frame bytes.
A subsequent message to the retained worker reads its live WASM allocation and
compares every byte after each failure. An initial failure leaves an empty host
empty; modifying a returned snapshot cannot change the host. Closing releases
the active worker and the bounded test process exits normally. The Python test
wrapper imposes a fifteen-second whole-control deadline.

Evidence: `research/evidence/live-wasm-swap-2026-10-10/manifest.json`; code:
`tools/re/reloop/live_wasm_host.js`. This is an owned reconstruction policy,
not recovered Xcode hot-reload sequencing or general SwiftUI state migration.
The native UI track could not run because the Mac was locked; no indirect
browser/UI workaround was attempted. Private bridge restoration is a separate
prerequisite. Scientific review and both milestones remain open. Next: integrate
the persistent host with a frozen source-build adapter and the complete native
extent corpus, add competing-proposal/close-during-proposal controls, then bind
the reviewed bounded adapter into the graph. Do not mark this task completed
from the two-fixture feasibility control.
