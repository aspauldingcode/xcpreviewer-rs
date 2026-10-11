# Frozen consolidated live-swap adapter

`liveswapprobe.corpus(out)` now runs the full anchored corpus, failure proposals,
close/quiescence controls and source-generation controls as one bounded adapter.
The standalone `tools/re/live-swap-probe.py` holds the exclusive controller lock,
copies executable sources into the output, and invokes only that frozen copy.
Fixtures require fixed external manifest anchors and full referenced-file hashes.
Each Node control has a bounded deadline; the whole frozen worker has 90 seconds.

Two frozen executions succeed, before and after adding owned-session timeout
cleanup. Both reproduce 84 complete independent allocations, 80 full reused
native allocations, six failed-proposal gates, four close controls and five
source-rejection gates. A separate process rehashes both seals and compares every
saved frame byte against its independent/native fixture. An actual timeout test
starts an owned parent/child session, enforces 0.2 seconds, and checks that the
child cannot write after its scheduled 0.6-second delay. No user application or
unrelated process receives a signal.

Receipt: `research/evidence/live-swap-adapter-verification-2026-10-10.json`.
This establishes a callable frozen adapter, not scheduler integration: explicit
worker/schema registration, campaign checks and canonical graph binding remain
pending. Existing staged controller changes are preserved. The adapter executes
owned reconstruction policy with reused public callback targets, not recovered
Canvas sequencing or native release acknowledgment. Scientific delivery review
and both milestone contracts remain open; no Xcode workspace was opened.
