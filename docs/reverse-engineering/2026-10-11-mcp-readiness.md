# Preview readiness versus retained diagnostic history

The owned MCP handler version is now 0.2.1. PreviewSession status, start, poll and
close results include `readiness`: state, frameRevision and a brief human-facing
message. This is an owned workflow policy. Native Canvas refresh, state reset or
wire semantics are not inferred from it.

A lastFailure diagnostic is historical. A later accepted publication makes the
preview ready even while that diagnostic remains retained. Consumers should use
readiness for their current display state and diagnostics for detailed history.
Initial build rejection is an ordinary completed tool result with readiness
failed and no frame; it is not necessarily a JSON-RPC or isError failure. Polling
a changed supported source can recover the same open session.

| State | Meaning |
| --- | --- |
| waiting | No accepted frame or current failure |
| building | Work active with no accepted frame |
| updating | Work active while the last frame remains available |
| failed | Current rejection/invalid/unavailable source with no accepted frame |
| stale | Current rejection/invalid/unavailable source while the last frame remains available |
| ready | Latest publication matches the accepted frame generation |
| closed | Session closed; open a new session to restart |

Messages describe the state without exposing compiler error paths. Generation
mismatch, missing publication and unknown empty-state inputs reject rather than
fabricating readiness. Nine owned policy cases and three invalid-state cases
replay in two fresh Node processes. Invalid/unavailable-source and active-build
rows are scoped policy controls, not newly measured native Canvas behavior.

The official client 2.3.1 used its actual stdio transport and default output-schema
validator against one owned server through the established wait-recording
supervisor. The source first rejected before any accepted frame. Changing it to
the supported 13×7 fixture produced revision 1, generation 2 and readiness ready,
while lastFailure retained generation 1. An unchanged poll returned identical
status and frame without rebuilding. A second unsupported edit produced stale
readiness with the original frame retained. The supported 11×6 edit recovered to
revision 2, generation 4 and ready, while lastFailure retained generation 3.
Close cleared availability and reported closed readiness.

Two supported edits produced two fresh Rust modules and actual successful CLI
waits 0; both intentionally unsupported attempts retain actual CLI waits 2 and
owned drain reports. The server's actual Node wait was 0 and final workers,
timers, building and busy counts were zero. All 15 correlated responses validate
against the pinned official initialize/tool-list/tool-result/JSON-RPC schemas and
stay within the existing reply cap. The independent Python reader compares all
65,536 consumer allocation bytes, including row padding and unused tails; two
fresh V8 instances independently render the saved modules against the finite
Python expectation. Compiler/source/module receipts and partial/final transcripts
correlate. The SDK's 1,108 installed files were rechecked before and after reuse;
no install, service purchase or global dependency change was needed.

Four resealed faults reject: recovered readiness incorrectly driven by historical
failure, wrong retained-frame generation, nonzero owned server wait, and a padded
row byte changed consistently across all retained packets/descriptors and partial
transcripts. The padding mutant also updates its allocation hash, so independent
expected bytes must reject it. No unplanned harness/native failure occurred in
this run. Both expected unsupported-source failures remain sealed. The isolated
candidate archive passes 91 Python plus seven Rust tests.

Evidence: `research/evidence/mcp-readiness-2026-10-11/manifest.json`, SHA-256
`9cdf028d82cdd2930879a26c5d0d1396bd26a48c3a48603c82439f78c2511b74`.

Next: discriminate file disappearance/empty source and same-source restoration,
then define refresh/reset consumer policy against separately scoped evidence.
The retained approved Xcode capture bridge remains offline, without restart or
permission bypass. Native R1/R2 release/reuse acceptance, actual Canvas transport,
modern MCP negotiation, platform delivery and both milestones remain open.
