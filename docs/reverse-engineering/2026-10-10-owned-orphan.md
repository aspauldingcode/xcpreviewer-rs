# Owned compiler target exit and inherited orphan cleanup

Two controls reproduce the prior runner's gap: a target exits0 or7 while its
forked child keeps stdout open. The runner notices a200ms deadline after the root
has exited, refuses to signal the retired numeric root PID, and settles around
845ms after the child writes its scheduled late marker. Both failures are retained.

A private Python supervisor now stays alive as the new POSIX group leader. It
starts the target within its inherited group, waits for the target, sends its
actual exit code over a separate descriptor and remains alive until the creator
terminates the still-owned group. Target subprocesses close that control descriptor.
The creator drains the group after success, failure, deadline or explicit abort,
then settles after supervisor exit and pipe closure. Numeric ownership is retained
through the anchor lifetime; no existing process lookup or attachment is used.

Both fixed root-exit controls suppress late writes and settle near100ms. Successful
target exit0 resolves; target exit7 rejects with7 preserved. Returned `code` is
the target status; `anchorCode` and `signal` describe the intentional supervisor
termination, and `pid` identifies the supervisor. SIGKILL on the owned anchor is
expected even after successful target completion. Escaping descendants remain
excluded; this does not establish arbitrary process-tree or native Canvas policy.

Canonical frozen run `20261011T042223Z-primary-live-wasm-swap-ddcf94bc` passes23
predeclared checks, including fresh compilation and the two orphan controls.
Fresh-process verification and separate full-byte checks cover84 independent,
80 reused-native and3 fresh compiler allocations. Evidence and failure/fix source
copies: `research/evidence/owned-orphan-2026-10-10`.

No user Xcode/simulator process was targeted. No Xcode workspace was opened,
private bridge restarted, or native Canvas lifecycle claim accepted. Both milestone
contracts and independent scientific delivery review remain open. The next
uncertainty is identity-aware observation of an owned child leaving the group.
