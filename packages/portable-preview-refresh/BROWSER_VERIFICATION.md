# Independent browser verification

Overall result: qualified PASS based on independent review of main-acquired permitted browser controls (see final section). This verifier’s own two executions were BLOCKED / inconclusive: neither produced a completed browser result or discriminated the mutation. Those original failures remain retained. No Canvas, pixel, native or broad browser parity claim follows.

## Scope and review

Inspected only the delivered browser-check.html and browser_check.py plus the previously reviewed delivered index.js. Imported Controller from /Users/8amps/xcpreviewer-rs/tools/re/reloop/core.py solely as experiment-lock infrastructure, inspecting its constructor and lock method to use the shared lock correctly. No research/private/product contents were read. No delegation, UI, Git or network research was used.

The HTML uses a real browser module script importing ./index.js, browser DOM output and ordinary JavaScript callbacks. It contains no Node runtime dependency or VM evaluation. It asserts nine lifecycle checks: initial, poll deduplication, explicit refresh, failure frame retention, rejected-source retry, recovery history, busy validation, close preventing late publication, and session independence.

The Python launcher invokes installed Chrome for Testing headless with a fresh temporary --user-data-dir, serves only its copied package over an ephemeral IPv4 loopback listener, and parses the browser's dumped DOM. It uses no --no-sandbox, disabled web security, remote-debugging connection to user browsers, or reuse of a user profile. This is intended actual browser execution, not a vm realm; the independent runs below did not reach a completed browser result.

Concrete boundedness improvement: changed the shared browser_check.py command budget from 30 to 25 seconds, reserving cleanup time within the requested 30-second job cap. Replaced unbounded post-kill communicate and wait with timeout=1. No delivered index.js changes. The timeout error now accurately identifies the 25-second command budget. Server shutdown and thread join remain cleanup work; an independent outer 30-second timeout also bounds each job. Unusual cleanup exceptions can still cause the harness to exit without its JSON, and no stronger universal termination guarantee is made.

Cleanup targets only process groups established by this launcher using start_new_session=True, and its own temporary profiles/server. It never searches for, matches by name, or kills user browser processes. Signals to the owned group and reaping of its root do not prove that a detached descendant cannot outlive it. The runs reported no process-tree observation; no all-descendants cleanup claim is made.

## Actual experiment

Command, run once:

`python3 independent-browser/run_verification.py`

The driver acquires Controller().lock() and runs exactly two serial jobs, each with subprocess timeout=30. Each uses a separate temporary copy of index.js, browser-check.html and browser_check.py. Positive uses unmodified implementation. Mutation changes only the temporary implementation's source-deduplication condition to false. The delivered implementation stays unchanged. A working harness should pass the first job and fail the second with error "poll deduplication".

Observed results:

- Positive: exit 1 after 1.9629682499999999 seconds; Chrome version command succeeded and returned Google Chrome for Testing 155.0.8059.39. Harness then reported `[Errno 1] Operation not permitted`, with empty stdout/stderr and no DOM/result.
- Deduplication-disabled mutation: exit 1 after 0.6712687499999999 seconds; same successful browser version and same permission error, with no DOM/result.
- Driver expected-discrimination assertion failed (exit 1), preserving the negative result accurately. Full machine-readable evidence is independent-browser-results.json beside this report.

The error was reported after the version command and before a completed DOM result; the harness does not report the failing stage more precisely. Do not interpret the environmental failure as either an implementation failure or a successful mutation test. No further browser jobs were attempted because the authorized two-job maximum was reached. The earlier builder's reported browser pass is separate evidence and was not independently reproduced here.

These checks concern JavaScript lifecycle behavior in a browser when runnable. They do not exercise Canvas drawing, pixels, Xcode, SwiftUI, native transport, native parity, or integration milestones.

## Review of main-acquired permitted controls

Subsequent evidence review updates the overall assessment: the main agent's correctly permitted browser run passes the nine lifecycle assertions, and its separately copied deduplication-disabled implementation is rejected at the expected assertion. I did not execute these browser runs. My original two sandbox EPERM failures above and their JSON remain unchanged.

Explicitly authorized additional review inputs were only these three owned records under /Users/8amps/xcpreviewer-rs/research/evidence/analysis-restoration-2026-10-15/: browser-positive.json, browser-mutant.json and browser-qualified-summary.json. The summary identifies two jobs in approved escalated execution under Controller, distinct from this verifier's sandboxed attempts. That acquisition/environment attribution comes from the main agent and retained summary; the JSON itself is not a cryptographic execution attestation.

Independent record checks, without another browser launch, parsed both JSON files and compared their complete embedded module-script text with delivered browser-check.html: both match exactly. Both record browser version Google Chrome for Testing 155.0.8059.39, successful version exit, and Chrome browser-process exit 0. Positive has outer harness exit 0, DOM data-status=pass, JSON status=pass and all nine expected check names. Mutation has outer harness exit 1 despite Chrome exit 0, DOM data-status=fail, JSON status=fail, only the initial check completed, and error "poll deduplication". Thus the retained mutation failed because of a behavioral assertion rather than a Chrome crash or incomplete page. Both records retain display-link diagnostic stderr; these did not prevent completion of the JavaScript assertions and do not establish rendering correctness.

The mutation metadata states "disable unchanged-poll deduplication". This agrees with the discriminating failure and the temporary-copy mutation design reviewed above. The records do not contain the mutated index.js or source hash, so mutation-source identity rests on the main agent's acquisition account and metadata; it is not independently reconstructable from dumped HTML alone.

This is substantive evidence that the reviewed browser harness detects a deduplication regression while the supplied unmodified implementation passes the named lifecycle cases in actual Chrome. It supports this limited actual-browser JavaScript lifecycle slice. It does not establish all contract behavior in browsers, cross-browser support, Canvas/pixel output, native protocol compatibility, Xcode/SwiftUI parity, or integration milestones. Cleanup attribution remains owned-root wait and owned-process-group signal only; the retained records do not prove all escaped descendants terminated. No production implementation edits, extra browser jobs, native/UI actions, Git or delegation occurred in this review.
