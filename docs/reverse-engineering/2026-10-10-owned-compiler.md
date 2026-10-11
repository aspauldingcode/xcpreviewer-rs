# Fresh compiler integration for owned file loops

`owned_compiler.compiler()` supplies a real builder to the finite source-file
loop. Each source is copied to a separate immutable build directory and passed
to the externally anchored frozen CLI. It validates source/module receipts,
frame-manifest hashes, generated payload hashes and every allocation byte against
an externally supplied independent oracle before proposing publication.

`runOwned()` starts only new POSIX process groups, limits stdout/stderr, enforces
a deadline, and propagates AbortSignal to the inherited owned group. It waits for
root exit and pipe closure before settling. This contract is for trusted compiler
roots that await their children; arbitrary escaping children and a root that
exits while a surviving child holds the pipes are not accepted. Safe orphan
identity/accounting is the next discriminating experiment. No existing user
process or application is targeted.

Standalone and canonical frozen executions each freshly compile three supported
file edits with zero cache hits. Their generated modules equal the pinned
reference modules; six complete saved allocations compare exactly (98,304 bytes).
An unsupported edit retains the exact last-good live frame. Real fork controls
confirm child startup and absence of scheduled late writes after group timeout
and explicit abort. A unit control verifies pre-aborted admission, bounded output
and successful normal completion.

Canonical run `20261011T041411Z-primary-live-wasm-swap-7262bae5` passes all21
predeclared checks, with fresh-process mechanical verification and separate byte
comparisons over84 independent and80 reused-native allocations. Evidence:
`research/evidence/owned-compiler-2026-10-10`. Runtime/compiler identities are
checked against frozen prerequisites and recorded. No new native callback or
Canvas capture occurs; scientific delivery review and both milestone contracts
remain open. No Xcode workspace was opened or private bridge restarted.
