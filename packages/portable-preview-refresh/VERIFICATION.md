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

## Additional isolated JavaScript realm experiment

Added test/portable-realm.test.js and performed one bounded experiment against the unchanged index.js module. The host test reads index.js, but evaluates its source using Node vm.SourceTextModule in a fresh vm context. The only injected runtime capability is the browser-standard AbortController API (provided by the Node host). Both static linking and dynamic import requests are denied; zero import requests occurred. Callbacks and lifecycle assertions execute inside the realm. The realm explicitly checks that process, Buffer and require are absent. The host subsequently exposes the evaluated createSession export to the realm as its test entry point.

Actual additional commands:

- `node --experimental-vm-modules --test test/portable-realm.test.js`: exit 0, 1 passed, 0 failed/skipped/cancelled; total duration 1194.433209 ms. Node emits its expected experimental VM Modules warning.
- `node --test`: exit 0, 19 discovered, 18 passed, 0 failed/cancelled, 1 skipped; total duration 2337.048791 ms. The new realm test explicitly skips without the VM Modules flag; its execution and pass are established by the preceding flagged command.

The experiment exercised initial empty state, first publication, unchanged poll deduplication, explicit unchanged refresh, rejected validation retaining the previous frame and revision, successful recovery retaining failure history, and terminal close aborting a pending build with late completion unable to publish. Final recovered session counters were revision 3, generation 4 and build count 4.

This establishes feasibility in a browser-like JavaScript realm without Node globals or module imports. It is not an actual browser execution or browser parity claim: the engine and AbortController provider remain Node, and no browser loader, DOM, UI, native integration, rendering or cross-browser behavior was tested. No implementation changes were needed. No network, native/UI tools, repository access or delegation was used for this experiment.
