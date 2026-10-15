# Independent delivery verification

Result: PASS for the bounded JavaScript contract in SPEC.md. No concrete implementation defect was found; index.js was not modified.

This serial verifier inspected only SPEC.md, index.js, package.json, README.md, PROVENANCE.md and the existing tests in this delivery directory. It added test/independent-verification.test.js with eight public-API tests. No repository research, target source, decompilation, network, native tools, UI, Git or delegated agents were used.

## Actual commands and results

Executed in /private/tmp/xcpreviewer-refresh-build-20261015:

- `node --version`: v24.19.0.
- `shasum -a 256 SPEC.md`: 7d74b65b4f00672387a911a24bc0dba63420d526c8bb4e912a286a077561d124, matching the implementation provenance record.
- `node --test`: exit 0; 18 tests passed, 0 failed, 0 skipped, 0 cancelled. This includes the 10 existing tests and 8 independent tests. Reported total duration: 1144.256667 ms.

The new tests discriminate synchronous build/validation reentrancy, generation accounting, busy rejection without changing the observed source or damaging a failing original attempt, awaited validation with truthy nonboolean rejection, synchronous close from either callback followed by late resolution or rejection, snapshot mutation isolation, and documented candidate reference ownership. Existing tests additionally cover retries/recovery, independent sessions, invalid sources, and external close during either callback phase.

## Findings and limitations

Only an exact true validation result publishes. Pending validation retains the accepted frame; busy calls neither start callbacks nor consume generations. Synchronous callback reentrancy sees the active operation. Close remains terminal even when called from inside a callback, and late rejection adds no ordinary failure record.

Status records and frame envelopes are fresh copies. Candidate payloads intentionally remain caller-owned references, as README.md explicitly documents; mutation of a returned object payload can change its contents without a new revision or validation. SPEC.md does not require cloning, deep immutability or protection against malicious callbacks. This is a documented boundary, not evidence that immutable frame contents are guaranteed.

Tests ran on Node 24.19.0 only, not every supported Node version. This verification is bounded behavioral evidence, not an exhaustive proof. It does not establish native compatibility, target parity, state preservation, integration acceptance, or either project's milestone.

PROVENANCE.md remains unchanged: its sole-input claim describes original implementation authorship. This verification subsequently used the delivered implementation, documentation and existing tests as review inputs in addition to SPEC.md. Directory/context separation was not externally enforced as a clean-room sandbox; nothing in this report upgrades that claim.
