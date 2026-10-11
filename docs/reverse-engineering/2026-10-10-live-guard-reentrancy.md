# Reentrant publication guard closure

The persistent host checked `closed` before invoking its publication guard. A
synchronous guard could call `close()` and return `true`. The proposal then
published its candidate and advanced the revision before a later assertion
rejected it. Although worker termination completed, a closed host retained a
snapshot backed by an exited worker.

Two discriminating controls reproduce this with an empty host and a previously
active host. Both old-source executions end with a non-null snapshot and an
unexpected revision increment. A second closed-state check immediately after
calling the guard now rejects before any publication mutation. Both fixed-source
controls end with null snapshots, unchanged revisions, zero workers and settled
operations. False, throwing and Promise-returning guards also reject while
preserving all 16,384 last-good bytes and the live instance.

The canonical `primary-live-wasm-swap` experiment now includes two closure
controls and three rejected-guard controls. Its changed experiment fingerprint
invalidates the previous completed overlay and requires a new frozen execution.
Run `20261011T035112Z-primary-live-wasm-swap-8279b44a` passes all ten declared
checks, with fresh-process mechanical verification and separate full-byte
comparison over 1,376,256 independent bytes and 1,310,720 reused native bytes.
Six host, source-revision and full-corpus regression tests pass.

Retained failure/fix source copies, exact results, and seal:
`research/evidence/live-guard-reentrancy-2026-10-10`. This is an owned callback
policy defect and reconstruction fix, not evidence of native Canvas callbacks,
resource release acknowledgments, browser behavior, or scientific delivery
acceptance. Both milestone contracts remain open. No Xcode workspace was opened.
