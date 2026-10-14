# Supervisor deadline with a SIGTERM-ignoring child

Two new owned controls leave the root running after the exit watcher releases its gate. The child installs SIG_IGN for SIGTERM before its readiness acknowledgement and creates its own session. The watcher validates both public birth identities and executable paths, registers NOTE_EXIT and NOTE_EXITSTATUS and remains alive while the existing supervisor reaches its configured deadline.

Both underlying supervisor receipts report failure `deadline`, drained true, target wait code -15, two tracked identities and zero remaining observed processes. Independent kernel events report root raw status15 followed by child raw status9. Python wait macros independently decode these as SIGTERM and SIGKILL respectively. Both watcher subprocesses actually return0. The production client retains `Error: Observed compiler failed: deadline`, without private abort or emergency closure. Empty output counts and SHA-256 values are independently checked. Fifteen resealed faults reject changed identities, topology, status, source, receipt, scope and diagnostics.

This qualifies bounded deadline drain for these observed owned identities. It does not establish child reaping, unseen escape coverage, actual Rust descendant wait outcomes, physical resource reclamation or native Canvas protocol acceptance. The evidence remains scoped to Darwin and the pinned Python/Node/public observer/watcher's identities. REA 6.2.0 is available independently of the absent approved private capture bridge; no bridge was restarted or workspace opened.

Evidence: `research/evidence/ignore-child-deadline-2026-10-14`, manifest SHA-256 `d7bf6100d00219454f30a3b7173b03e6556e31d9cb50b20c4e29d41cfcf81bae`. The acquisition uses two slots, 15-second outer deadlines, a 3-second supervisor configuration and a 4-second kernel watcher deadline. Verification never repeats native acquisition. Prior root-first failure controls remain sealed unchanged.

Next: independently discriminate private client abort from supervisor deadline using the same ignoring-child fixture; retain cleanup and reaping distinctions. Both milestones remain open.
