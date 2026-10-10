# Extent CLI verifier and process-observation failure

Implemented a bounded consumer of the separately sealed source-frame CLI and
native extent references. It executes the frozen CLI, not concurrently edited
workspace code. The declared acceptance denominator is 80 full native target
allocations across 40 extent jobs, four independent transparent frames, 84
independently decoded PNGs, pixel/padding/tail/PNG-alpha corruption controls and
eight source/runtime/cache/publication failure controls. PNG expectations use a
separate Fraction projection; native callback bytes and PNG conversion claims
remain distinct. Compiler, linker, Node and both prerequisite manifest hashes
must match their sealed identities before reuse.

The complete experiment did not pass. Three attempts stopped at the process
observer, with two, four and zero retained partial frames. None completes the
extent contract; the graph remains open. The first controller exception propagated
from a two-second `ps` timeout, leaving an unfinished manifest. Owned descendants
were drained; the original graph wake was resumed with its original deadline and
reconciled the interrupted run. No manifest was manually edited, failure ledger
cleared, experiment deadline raised or unknown/user process terminated.

The controller now records `subprocess.TimeoutExpired` as failed execution and
retains cleanup diagnostics, allowing this observation failure to seal normally.
A separate ownership change reads a minimal ancestry/start-time inventory and
fetches command identities only for candidate owned ancestry. Full start/command
identity checks still guard signals to previously observed PIDs. Start changes
between the inventory and command read are rejected; detached descendants remain
tracked. Each subprocess read retains its two-second limit. This is an owned
process observer, not arbitrary process discovery or native Canvas evidence.

A discriminating read-only diagnostic measured minimal inventory at 0.150 seconds
(658 rows) and an owned-PID command query at 0.025 seconds. However, the subsequent
serialized extent run also timed out on the minimal inventory. Thus full command
retrieval alone is not an adequate explanation. Concurrent validation was present
in the first attempt but its removal did not resolve the failure. The host
observation prerequisite remains unreliable; do not repeat unchanged expensive
extent attempts. A future public macOS libproc observer can be implemented and
compared against independently observed owned process identities before retrying.

Nine targeted tests pass, including reused identity exclusion, between-read start
changes, owned root exec, detached-child quiescence, timeout retention, Fraction
PNG projection, profile/format rejection and strict adapter selection. The earlier
isolated proposed extent verifier passed 320 repository tests. Final serial
validation of the isolated observer/verifier implementation passed 323 tests in
96.324 seconds, excluding all unrelated concurrent changes.
Tests are implementation controls, not full native extent or delivery acceptance.

All three failed/interrupted runs are retained with separately pinned, valid seals
in [the sanitized receipt](../../research/evidence/extent-cli-observation-2026-10-10.json).
No browser or Xcode windows opened. No Apple binaries or private dumps published.
Both milestones remain open. The next research task is the process-observation
oracle; the complete extent consumer remains blocked on that prerequisite.
